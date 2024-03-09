"""
    Copyright 2023 Guillaume Everarts de Velp

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


        host = std::Host(
            name="localhost",
            remote_agent=true,
            ip="127.0.0.1",
            os=std::linux,
        )

        podman::ImageFromSource(
            host=host,
            name="docker.io/library/alpine:latest",
            context="https://github.com/alpinelinux/docker-alpine.git",
            file="Dockerfile",
            purged={json.dumps(purged)},
        )
    """

    project.compile(model, no_dedent=False)


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
