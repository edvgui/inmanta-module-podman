"""
Copyright 2026 Guillaume Everarts de Velp

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

import pathlib

from pytest_inmanta.plugin import Project


def update_example(name: str, model: str) -> None:
    """
    Find the example with the given name in the readme, and make sure
    the model is the described one.
    """
    readme_file = pathlib.Path(__file__).parent.parent / "README.md"
    readme = readme_file.read_text()

    marker_start = f"<x-example-{name}>"
    start = readme.find(marker_start)
    if start == -1:
        raise RuntimeError(
            f"Can not find marker {marker_start} in readme {readme_file}"
        )

    marker_end = f"</x-example-{name}>"
    end = readme.find(marker_end, start)
    if end == -1:
        raise RuntimeError(f"Can not find marker {marker_end} in readme {readme_file}")

    current_model = readme[start : end + len(marker_end)]
    desired_model = marker_start + "\n\n```\n" + model + "\n```\n\n" + marker_end

    if current_model != desired_model:
        readme_file.write_text(
            readme[:start] + desired_model + readme[end + len(marker_end) :]
        )


def test_quadlet(project: Project) -> None:

    model = """
        import mitogen
        import podman
        import podman::container_like
        import podman::services
        import std

        host = std::Host(
            name="localhost",
            os=std::linux,
            via=mitogen::Local(),
        )

        # Make sure the container image is present on the host
        image = podman::ImageFromRegistry(
            host=host,
            name="docker.io/library/nginx:latest",
        )

        # Define the container
        web = podman::Container(
            host=host,
            name="nginx-web",
            image=image.name,
            publish=[
                podman::container_like::Publish(host_port="8080", container_port="80"),
            ],
        )

        # Wrap the container into a systemd service, using a quadlet unit file
        podman::services::SystemdContainer(
            container=web,
            state="running",
            enabled=true,
            systemd_unit_dir="/etc/systemd/system",
            systemd_container_dir="/etc/containers/systemd",
            quadlet=true,
        )
    """

    project.compile(model, no_dedent=False)

    # Verify the image resource is exported
    image = project.get_resource("podman::ImageFromRegistry")
    assert image is not None

    # Verify the quadlet unit file is generated and has the expected content
    quadlet_path = "/etc/containers/systemd/container-nginx-web.container"
    unit_file_resource = next(
        r
        for r in project.resources.values()
        if getattr(r, "path", None) == quadlet_path
    )
    content = unit_file_resource.content
    expected = [
        "[Container]",
        "ContainerName=nginx-web",
        "Image=docker.io/library/nginx:latest",
        "PublishPort=8080:80",
    ]
    missing = [token for token in expected if token not in content]
    assert not missing, f"missing tokens in unit file: {missing}\ncontent:\n{content}"

    tested_model = pathlib.Path(project._test_project_dir, "main.cf").read_text()
    update_example("quadlet", tested_model)
