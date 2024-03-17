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
import re

import pydantic

import inmanta.agent.handler
import inmanta.const
import inmanta.data.model
import inmanta.execute.proxy
import inmanta.export
import inmanta.resources
import inmanta_plugins.podman.resources.abc


@inmanta.resources.resource(
    name="podman::ImageDiscovery",
    id_attribute="q",
    agent="host.name",
)
class ImageDiscoveryResource(
    inmanta_plugins.podman.resources.abc.ResourceABC,
    inmanta.resources.DiscoveryResource,
):
    pass


class DiscoveredImage(pydantic.BaseModel):
    name: str
    owner: str
    digest: str
    config: dict


@inmanta.agent.handler.provider("podman::ImageDiscovery", "")
class ImageDiscoveryHandler(
    inmanta_plugins.podman.resources.abc.HandlerABC[ImageDiscoveryResource],
    inmanta.agent.handler.DiscoveryHandler[ImageDiscoveryResource, DiscoveredImage],
):
    def discover_resources(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        discovery_resource: ImageDiscoveryResource,
    ) -> collections.abc.Mapping[inmanta.data.model.ResourceIdStr, DiscoveredImage]:
        # Run the ls command on the remote host
        command = [
            "podman",
            "image",
            "ls",
            "--format=json",
            "--filter=dangling=false",
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
            raise RuntimeError("Failed to inspect images")

        # Build the reference expression we should use to filter out some
        # images
        image_reference_expression = re.compile(discovery_resource.name)

        # Build the discovered resource objects
        return {
            inmanta.resources.Id(
                "podman::ImageFromRegistry",
                discovery_resource.id.agent_name,
                "q",
                f"owner={discovery_resource.owner}&name={image_name}",
            ).resource_str(): DiscoveredImage(
                config=image,
                name=image_name,
                owner=discovery_resource.owner,
                digest=image["Digest"],
            )
            for image in json.loads(stdout)
            for image_name in image["Names"]
            if image_reference_expression.fullmatch(image_name)
        }
