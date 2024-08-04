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
            name="docker.io/library/alpine:latest",
            digest={repr(digest) if digest is not None else "null"},
            purged={json.dumps(purged)},
        )

        podman::ImageDiscovery(
            host=host,
            name=".*",
        )
    """

    project.compile(model, no_dedent=False)


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
