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

from pytest_inmanta.plugin import Project


def test_publish_same_container_port(project: Project) -> None:
    """
    A container port can be published more than once: over both tcp and udp
    (e.g. dns), or on several host ports and addresses.  Every option left
    unset is left to podman's default.
    """
    model = """
        import mitogen
        import podman
        import podman::container_like
        import std

        host = std::Host(
            name="localhost",
            os=std::linux,
            via=mitogen::Local(),
        )

        dns = podman::Container(
            host=host,
            name="dns",
            image="docker.io/adguard/adguardhome:latest",
            publish=[
                podman::container_like::Publish(container_port="53"),
                podman::container_like::Publish(
                    host_port="53",
                    container_port="53",
                    protocol="tcp",
                ),
                podman::container_like::Publish(
                    host_port="53",
                    container_port="53",
                    protocol="udp",
                ),
                podman::container_like::Publish(
                    ip="127.0.0.1",
                    host_port="5353",
                    container_port="53",
                    protocol="udp",
                ),
                podman::container_like::Publish(
                    ip="::1",
                    host_port="5353",
                    container_port="53",
                    protocol="udp",
                ),
            ],
        )
    """

    project.compile(model, no_dedent=False)

    (dns,) = project.get_instances("podman::Container")
    assert sorted(publish.cli_option for publish in dns.publish) == sorted(
        [
            "53",
            "53:53/tcp",
            "53:53/udp",
            "127.0.0.1:5353:53/udp",
            "[::1]:5353:53/udp",
        ]
    )
