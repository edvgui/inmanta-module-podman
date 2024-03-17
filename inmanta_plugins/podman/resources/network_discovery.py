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

import collections.abc
import json

import pydantic

import inmanta.agent.handler
import inmanta.const
import inmanta.data.model
import inmanta.execute.proxy
import inmanta.export
import inmanta.resources
import inmanta_plugins.podman.resources.abc


@inmanta.resources.resource(
    name="podman::NetworkDiscovery",
    id_attribute="q",
    agent="host.name",
)
class NetworkDiscoveryResource(
    inmanta_plugins.podman.resources.abc.ResourceABC,
    inmanta.resources.DiscoveryResource,
):
    pass


class DiscoveredNetwork(pydantic.BaseModel):
    config: dict
    name: str
    owner: str


@inmanta.agent.handler.provider("podman::NetworkDiscovery", "")
class NetworkDiscoveryHandler(
    inmanta_plugins.podman.resources.abc.HandlerABC[NetworkDiscoveryResource],
    inmanta.agent.handler.DiscoveryHandler[NetworkDiscoveryResource, DiscoveredNetwork],
):
    def discover_resources(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        discovery_resource: NetworkDiscoveryResource,
    ) -> collections.abc.Mapping[inmanta.data.model.ResourceIdStr, DiscoveredNetwork]:
        # Run the ls command on the remote host
        command = [
            "podman",
            "network",
            "ls",
            "--format=json",
            f"--filter=name={discovery_resource.name}",
        ]
        stdout, stderr, ret = self.run_command(
            ctx,
            discovery_resource,
            command=command,
            timeout=5,
        )

        # If the command failed, something went wrong
        if ret != 0:
            ctx.error(
                "%(stderr)s",
                exit_code=ret,
                stderr=stderr,
            )
            raise RuntimeError("Failed to inspect networks")

        # Build the discovered resource objects
        return {
            inmanta.resources.Id(
                "podman::Network",
                discovery_resource.id.agent_name,
                "q",
                f"owner={discovery_resource.owner}&name={network['name']}",
            ).resource_str(): DiscoveredNetwork(
                config=network,
                name=network["name"],
                owner=discovery_resource.owner,
            )
            for network in json.loads(stdout)
        }
