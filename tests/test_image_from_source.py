"""
Copyright 2025 Guillaume Everarts de Velp

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contact: edvgui@gmail.com
"""

import json

from pytest_inmanta.plugin import Project

import inmanta.const


def test_model(project: Project, purged: bool = False) -> None:
    model = f"""
        import podman
        import podman::network
        import std
        import mitogen


        host = std::Host(
            name="localhost",
            remote_agent=true,
            ip="127.0.0.1",
            os=std::linux,
            via=mitogen::Local(),
        )

        podman::ImageFromSource(
            host=host,
            name="ghcr.io/linuxcontainers/alpine:latest",
            context="https://github.com/alpinelinux/docker-alpine.git",
            file="Dockerfile",
            purged={json.dumps(purged)},
        )
    """

    project.compile(model, no_dedent=False)


def test_build_timeout(project: Project) -> None:
    # Build an image from a context that can not be reached, with a very
    # short timeout.  The build command hangs trying to fetch the context,
    # so the timeout aborts it and the deployment must fail explicitly.
    model = """
        import podman
        import std
        import mitogen


        host = std::Host(
            name="localhost",
            remote_agent=true,
            ip="127.0.0.1",
            os=std::linux,
            via=mitogen::Local(),
        )

        podman::ImageFromSource(
            host=host,
            name="inmanta/does-not-exist:latest",
            # RFC 5737 TEST-NET-1 address, guaranteed not to be routable, so the
            # build hangs fetching the context until our timeout kicks in.
            context="https://192.0.2.1/inmanta/does-not-exist.git",
            build_timeout=1,
        )
    """

    project.compile(model, no_dedent=False)

    resource = project.get_resource("podman::ImageFromSource")
    assert resource is not None
    assert resource.build_timeout == 1

    result = project.deploy_resource_v2(
        "podman::ImageFromSource",
        expected_status=inmanta.const.ResourceState.failed,
    )

    # The failure must clearly point at the build command timing out after the
    # configured duration.
    result.assert_has_logline(r"podman.*build.*timed out after 1 seconds")


def test_deploy(project: Project) -> None:
    # Build the alpine image
    test_model(project, purged=False)
    project.deploy_resource("podman::ImageFromSource")

    # We can't make a dryrun, but we can assert that rebuilding the
    # image didn't bring any change
    project.deploy_resource(
        "podman::ImageFromSource", change=inmanta.const.Change.nochange
    )

    # Make sure the image is gone
    test_model(project, purged=True)
    assert project.dryrun_resource("podman::ImageFromSource")
    project.deploy_resource("podman::ImageFromSource")
    assert not project.dryrun_resource("podman::ImageFromSource")
