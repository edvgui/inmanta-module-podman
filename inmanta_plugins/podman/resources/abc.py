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

import typing

import inmanta.agent.handler
import inmanta.execute.proxy
import inmanta.export
import inmanta.resources


class ResourceABC(inmanta.resources.PurgeableResource):
    fields = (
        "owner",
        "name",
    )
    owner: str
    name: str

    @classmethod
    def get_q(
        cls,
        exporter: inmanta.export.Exporter,
        entity: inmanta.execute.proxy.DynamicProxy,
    ) -> str:
        return f"owner={entity.owner}&name={entity.name}"


ABC = typing.TypeVar("ABC", bound=ResourceABC)


class HandlerABC(typing.Generic[ABC]):
    def run_command(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ABC,
        *,
        command: list[str],
        timeout: typing.Optional[int],
        cwd: typing.Optional[str] = None,
        env: dict[str, str] = {},
        run_as: typing.Optional[str] = None,
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
        :param run_as: The user that should be running the command, defaults to the
            resource owner.
        """
        if run_as is None:
            run_as = str(resource.owner)

        # The io helper will always run command as root, if we want to use another
        # user, we have to use sudo to change user.
        if run_as != "root":
            command = ["sudo", "-E", "-u", run_as, "--", *command]

        # Run the command on the host
        stdout, stderr, return_code = self._io.run(
            command[0], command[1:], env or None, cwd, timeout=timeout
        )

        # Log the command output
        ctx.debug(
            "%(cmd)s",
            cmd=str(command),
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
        )

        return stdout, stderr, return_code
