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


def test_model(
    project: Project, purged: bool = False, digest: str | None = None
) -> None:
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

        podman::ImageFromRegistry(
            host=host,
            name="ghcr.io/linuxcontainers/alpine:latest",
            digest={repr(digest) if digest is not None else "null"},
            purged={json.dumps(purged)},
        )

        podman::ImageDiscovery(
            host=host,
            name=".*",
        )
    """

    project.compile(model, no_dedent=False)


def test_pull_timeout(project: Project) -> None:
    # Pull an image from a registry that can not be reached, with a very
    # short timeout.  The pull command hangs trying to connect, so the
    # timeout aborts it and the deployment must fail explicitly.
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

        podman::ImageFromRegistry(
            host=host,
            # RFC 5737 TEST-NET-1 address, guaranteed not to be routable, so the
            # pull hangs on connection until our timeout kicks in.
            name="192.0.2.1:5000/inmanta/does-not-exist:latest",
            pull_timeout=1,
        )
    """

    project.compile(model, no_dedent=False)

    resource = project.get_resource("podman::ImageFromRegistry")
    assert resource is not None
    assert resource.pull_timeout == 1

    result = project.deploy_resource_v2(
        "podman::ImageFromRegistry",
        expected_status=inmanta.const.ResourceState.failed,
    )

    # The failure must clearly point at the pull command timing out after the
    # configured duration.
    result.assert_has_logline(r"podman.*pull.*timed out after 1 seconds")


def test_deploy(project: Project) -> None:
    # Make sure the busybox image is there
    test_model(project, purged=False)

    # Resolve the image id
    image_resource = project.get_resource("podman::ImageFromRegistry")
    assert image_resource is not None
    image_resource_id = image_resource.id.resource_str()

    # Make sure the image gets deployed, we don't force the digest, the image should
    # always detect a change
    assert project.dryrun_resource("podman::ImageFromRegistry")
    project.deploy_resource("podman::ImageFromRegistry")
    assert project.dryrun_resource("podman::ImageFromRegistry")

    # Check that the discovery resource finds our image as well
    result = project.deploy_resource_v2("podman::ImageDiscovery")
    result.assert_status()
    images = {res.discovered_resource_id: res for res in result.discovered_resources}
    assert image_resource_id in images

    # Make sure that when we set the digest, the resource doesn't need to
    # be deployed again
    test_model(project, digest=images[image_resource_id].values["digest"])
    assert not project.dryrun_resource("podman::ImageFromRegistry")

    # Make sure the image is gone
    test_model(project, purged=True)
    assert project.dryrun_resource("podman::ImageFromRegistry")
    project.deploy_resource("podman::ImageFromRegistry")
    assert not project.dryrun_resource("podman::ImageFromRegistry")

    # Check that the discovery resource finds our image as well
    result = project.deploy_resource_v2("podman::ImageDiscovery")
    result.assert_status()
    discovered_resources = [
        res.discovered_resource_id for res in result.discovered_resources
    ]
    assert image_resource_id not in discovered_resources
