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
import typing

import inmanta.agent.handler
import inmanta.const
import inmanta.execute.proxy
import inmanta.export
import inmanta.resources
import inmanta_plugins.podman.resources.abc


def merge(
    base_config: typing.Union[dict, list[dict], object],
    config: typing.Union[dict, list[dict], object],
) -> typing.Union[dict, list[dict], object]:
    """
    Merge the config into the base_config.  This is similar to calling the
    update method of a dict, except that we are here merging lists as well.

    :param base_config: The base config, that we want to update with our config
    :param config: The config whose content we want to insert into the base
        config.
    """
    if config is None:
        # If config doesn't have a value for this, we don't diverge from
        # the base config
        return base_config

    if isinstance(base_config, dict):
        # If the base config is a dict, we should try to merge each key of
        # the dict that exists in the base config
        assert isinstance(config, dict), type(config)
        return {k: merge(v, config.get(k)) for k, v in base_config.items()}

    if isinstance(base_config, list):
        # If the base config is a list, we should try to compare the list
        # to the config list.
        assert isinstance(config, list), type(config)
        if len(base_config) != len(config):
            # The lists don't have the same length, we don't bother
            # matching elements one-to-one
            return config

        # Assume the elements are ordered and merge them together
        return [merge(base_config[i], config[i]) for i in range(len(base_config))]

    return config


@inmanta.resources.resource(
    name="podman::Network",
    id_attribute="q",
    agent="host.name",
)
class NetworkResource(inmanta_plugins.podman.resources.abc.ResourceABC):
    fields = ("config",)
    config: dict

    @classmethod
    def get_config(
        cls,
        exporter: inmanta.export.Exporter,
        entity: inmanta.execute.proxy.DynamicProxy,
    ) -> dict:
        """
        Build the network expected config, as should be returned by the inspect
        command.
        """
        config = {
            "name": entity.name,
            "driver": entity.driver,
            "ipv6_enabled": entity.ipv6_enabled,
            "internal": entity.internal,
            "dns_enabled": entity.dns_enabled,
        }
        if entity.subnets:
            config["subnets"] = [
                {
                    "subnet": sub.subnet,
                    "gateway": sub.gateway,
                }
                for sub in entity.subnets
            ]

        return config


def build_create_command(config: dict) -> list[str]:
    """
    Helper method to build the podman network create command based on
    the config that can be read from the resource.

    :param config: The config that should be converted to a create command.
    """
    # Build the create command
    cmd = ["podman", "network", "create"]

    if config["driver"] is not None:
        cmd.extend(["--driver", config["driver"]])

    if config["ipv6_enabled"]:
        cmd.append("--ipv6")

    if config["internal"]:
        cmd.append("--internal")

    if not config["dns_enabled"]:
        cmd.append("--disable-dns")

    if "subnets" in config:
        # Create the subnets list
        subnets = [sub["subnet"] for sub in config["subnets"]]
        cmd.extend(["--subnet", ",".join(subnets)])

        # Create the gateways list
        gateways = [
            sub["gateway"]
            for sub in config["subnets"]
            if sub.get("gateway", None) is not None
        ]
        if gateways:
            cmd.extend(["--gateway", ",".join(gateways)])

    cmd.append(config["name"])

    return cmd


@inmanta.agent.handler.provider("podman::Network", "")
class NetworkHandler(
    inmanta_plugins.podman.resources.abc.HandlerABC[NetworkResource],
    inmanta.agent.handler.CRUDHandlerGeneric[NetworkResource],
):
    def calculate_diff(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        current: NetworkResource,
        desired: NetworkResource,
    ) -> dict[str, dict[str, object]]:
        diff = super().calculate_diff(ctx, current, desired)
        if "config" not in diff:
            return diff

        updated_config = merge(current.config, desired.config)
        if current.config == updated_config:
            # If by applying the desired state to the current config
            # (using the merge helper) we don't detect any change, then
            # our desired state doesn't differ from the current state
            del diff["config"]
        else:
            # Overwrite the natural diff by the merge diff that we did
            # for better traceability
            diff["config"] = {
                "desired": updated_config,
                "current": current.config,
            }

        return diff

    def read_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: NetworkResource,
    ) -> None:
        # Run the inspect command on the remote host
        command = ["podman", "network", "inspect", resource.name]
        stdout, stderr, ret = self.run_command(
            ctx,
            resource,
            command=command,
            timeout=5,
        )

        # If we receive an empty list, our network doesn't exist
        if stdout.strip() == "[]":
            ctx.info("%(stderr)s", stderr=stderr)
            raise inmanta.agent.handler.ResourcePurged()

        # If the command failed, something went wrong
        if ret != 0:
            ctx.error(
                "%(stderr)s",
                exit_code=ret,
                stderr=stderr,
            )
            raise RuntimeError("Failed to inspect network")

        # Load the inspect result
        resource.config = json.loads(stdout)[0]

    def create_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: NetworkResource,
    ) -> None:
        # Run the create command on the remote host
        command = build_create_command(resource.config)
        _, stderr, ret = self.run_command(
            ctx,
            resource,
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
            raise RuntimeError("Failed to create network")

        ctx.set_created()

    def update_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        changes: dict[str, dict[str, object]],
        resource: NetworkResource,
    ) -> None:
        # We can't update the network, se we first delete it, then re-create it
        self.delete_resource(ctx, resource)

        # Reset change value to make sure we can call create_resource
        ctx._change = inmanta.const.Change.nochange

        # Re-create the network
        self.create_resource(ctx, resource)

        # Reset change value so that we can set our resource as updated
        ctx._change = inmanta.const.Change.nochange

        ctx.set_updated()

    def delete_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: NetworkResource,
    ) -> None:
        # Run the create command on the remote host
        command = ["podman", "network", "remove", resource.name]
        _, stderr, ret = self.run_command(
            ctx,
            resource,
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
            raise RuntimeError("Failed to remove network")

        ctx.set_purged()
