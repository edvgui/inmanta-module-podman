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


def test_model(project: Project, purged: bool = False) -> None:
    model = f"""
        import podman
        import podman::network
        import std

        user = std::get_env("USER")

        host = std::Host(
            name="localhost",
            remote_agent=true,
            remote_user=user,
            ip="127.0.0.1",
            os=std::linux,
        )

        podman::Network(
            host=host,
            name="test-net",
            subnets=[Subnet(subnet="172.45.0.0/24")],
            purged={json.dumps(purged)},
        )
    """

    project.compile(model, no_dedent=False)


def test_deploy(project: Project) -> None:
    # Make sure the network is there
    test_model(project, purged=False)
    project.deploy_resource("podman::Network")
    assert not project.dryrun_resource("podman::Network")

    # Make sure the network is gone
    test_model(project, purged=True)
    assert project.dryrun_resource("podman::Network")
    project.deploy_resource("podman::Network")
    assert not project.dryrun_resource("podman::Network")
