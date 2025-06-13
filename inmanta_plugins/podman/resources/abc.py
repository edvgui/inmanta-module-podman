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

import typing

import inmanta_plugins.mitogen.abc

import inmanta.agent.handler
import inmanta.execute.proxy
import inmanta.export
import inmanta.resources


class ResourceABC(
    inmanta.resources.ManagedResource,
    inmanta_plugins.mitogen.abc.Resource,
):
    fields = (
        "owner",
        "name",
    )
    owner: str | None
    name: str

    @classmethod
    def get_uri(
        cls,
        exporter: inmanta.export.Exporter,
        entity: inmanta.execute.proxy.DynamicProxy,
    ) -> str:
        if entity.owner is None:
            return entity.name
        else:
            return f"{entity.owner}:{entity.name}"


ABC = typing.TypeVar("ABC", bound=ResourceABC)


class HandlerABC(inmanta_plugins.mitogen.abc.Handler[ABC]):
    def whoami(self) -> str:
        """
        Check which user is currently executing the commands on the remote host.
        """
        # Cache the result of the call on the proxy session, as the same proxy
        # will always bring us to the same user
        if hasattr(self.proxy, "_whoami"):
            return getattr(self.proxy, "_whoami")

        stdout, stderr, ret = self.proxy.run("whoami")
        if ret == 0:
            setattr(self.proxy, "_whoami", stdout)
            return stdout

        raise RuntimeError(
            f"Failed to check current user: {stderr} (error code: {ret})"
        )

    def run_command(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ABC,
        *,
        command: list[str],
        timeout: typing.Optional[int],
        cwd: typing.Optional[str] = None,
        env: dict[str, str] = {},
    ) -> tuple[str, str, int]:
        """
        Execute a command on the host targeted by the agent, and return the result.
        The returned value is a tuple containing in that order: stdout, stderr, return code.

        :param ctx: The handler context object used by the handler at runtime
        :param resource: The resource object used by the handler at runtime
        :param command: The command to run on the host
        :param timeout: The maximum duration the command can take to run
        :param cwd: The directory in which the command should be executed
        :param env: Some environment variables to pass to the command
        """
        # We always want to run the command as the resource owner.
        # Case 1: The owner is not set on the resource, then the owner of the
        #   resource is implicitly the user of the proxy, we can execute the
        #   command as is.
        # Case 2: The owner is set and matches the user of the proxy, we can
        #   execute the command as is.
        # Case 3: The owner is set and is different from the user of the proxy,
        #   we have to use sudo to execute the command as the resource owner.

        if resource.owner is None:
            pass
        elif resource.owner == self.whoami():
            pass
        else:
            command = ["sudo", "--login", "-u", resource.owner, "--", *command]

        # Run the command on the host
        stdout, stderr, return_code = self.proxy.run(
            command[0],
            command[1:],
            env or None,
            cwd,
            timeout=timeout,
        )

        return stdout, stderr, return_code
