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


def test_model(
    project: Project,
    purged: bool = False,
    subnets: list[str] = ["172.45.0.0/24"],
    routes: list[dict] = ["10.0.0.0/24"],
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

        podman::Network(
            host=host,
            name="test-net",
            subnets=[
                Subnet(subnet=s)
                for s in {json.dumps(subnets)}
            ],
            routes=[
                Route(destination=d, gateway="172.45.0.3")
                for d in {json.dumps(routes)}
            ],
            options={{"isolate": "true"}},
            labels={{"test": "a"}},
            purged={json.dumps(purged)},
        )

        podman::NetworkDiscovery(
            host=host,
            name=".*",
        )
    """

    project.compile(model, no_dedent=False)


def test_deploy(project: Project) -> None:
    # Make sure the network is there
    test_model(project, purged=False)

    # Resolve the network id
    network_resource = project.get_resource("podman::Network")
    assert network_resource is not None
    network_resource_id = network_resource.id.resource_str()

    # Make sure the network gets deployed
    project.deploy_resource("podman::Network")
    assert not project.dryrun_resource("podman::Network")

    # Check that the discovery resource finds our network as well
    result = project.deploy_resource_v2("podman::NetworkDiscovery")
    result.assert_status()
    discovered_resources = [
        res.discovered_resource_id for res in result.discovered_resources
    ]
    assert network_resource_id in discovered_resources

    # Update the network, add a subnet and a route
    test_model(
        project,
        purged=False,
        subnets=["172.45.0.0/24", "172.46.0.0/24"],
        routes=["10.0.0.0/24", "192.168.1.0/24"],
    )
    assert project.dryrun_resource("podman::Network")
    project.deploy_resource("podman::Network")
    assert not project.dryrun_resource("podman::Network")

    # Check that a desired state with less subnets and routes
    # doesn't cause any changes
    test_model(project, purged=False)
    assert not project.dryrun_resource("podman::Network")

    # Make sure the network is gone
    test_model(project, purged=True)
    assert project.dryrun_resource("podman::Network")
    project.deploy_resource("podman::Network")
    assert not project.dryrun_resource("podman::Network")

    # Check that the discovery resource finds our network as well
    result = project.deploy_resource_v2("podman::NetworkDiscovery")
    result.assert_status()
    discovered_resources = [
        res.discovered_resource_id for res in result.discovered_resources
    ]
    assert network_resource_id not in discovered_resources
