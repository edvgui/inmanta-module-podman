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

import shlex
import typing

import inmanta.plugins


@inmanta.plugins.plugin()
def removesuffix(s: "string", suffix: "string") -> "string":  # type: ignore
    """
    Remove the given suffix from the input string.

    :param s: The string that should remove the suffix from.
    :param suffix: The suffix to remove from the string, if it has it.
    """
    return str(s).removesuffix(suffix)


@inmanta.plugins.plugin()
def shlex_join(cmd: "string[]") -> "string":  # type: ignore
    """
    Join all the parts of the command into a string that can safely be parsed
    by a shell as a valid command.

    :param cmd: All the parts of the command
    """
    return shlex.join(cmd)


@inmanta.plugins.plugin()
def plus(a: "int", b: "int") -> "int":
    """
    Will be replaced by https://github.com/inmanta/inmanta-core/issues/1799
    """
    return a + b


@inmanta.plugins.plugin()
def minus(a: "int", b: "int") -> "int":
    """
    Will be replaced by https://github.com/inmanta/inmanta-core/issues/1799
    """
    return a - b


@inmanta.plugins.plugin()
def inline_options(options: "dict") -> "string":  # type: ignore
    """
    Convert a dict of options into a comma-separated list of key=value pairs.

    :param options: The options dict to serialize into a string.
    """
    return ",".join(f"{k}={v}" for k, v in options.items() if v is not None)


@inmanta.plugins.plugin()
def join(parts: "string[]", *, separator: "string") -> "string":  # type: ignore
    """
    Join all the elements in the list together, use the separator in
    between each joined part.

    :param parts: The list of string we want to join
    :param separator: The separator to use in the join
    """
    return separator.join(parts)


def option(name: str, value: str | int | None) -> typing.Optional[str]:
    """
    Helper function to create a cli option with the given name and value,
    or None if the value is None.

    :param name: The name of the cli option
    :param value: The value of the cli option
    """
    return f"--{name}={value}" if value is not None else None


def options(name: str, values: typing.Sequence[object]) -> typing.Sequence[str]:
    """
    Helper function to a repeating cli option, based on the given sequence
    of objects.  The provided object should have the `cli_option` attribute,
    providing the value for the option.

    :param name: The name of the cli option
    :param values: The list of objects
    """
    return [f"--{name}={value.cli_option}" for value in values]


def extra_args(command: str, args: typing.Sequence[object]) -> typing.Sequence[str]:
    """
    Helper function to provide the list of serialized extra arguments assigned
    to a container like entity, for a specific command.

    :param command: The command which wants to fetch all the special arguments.
    :param args: The full set of arguments which might contain extra arguments
        for our command.
    """
    return [
        f"--{arg.name}={arg.value}" if arg.value is not None else f"--{arg.name}"
        for arg in args
        if arg.cmd == command
    ]


@inmanta.plugins.plugin()
def container_rm(
    container: "podman::Container",  # type: ignore
    *,
    force: "bool" = False,
    ignore: "bool" = False,
    cidfile: "string?" = None,  # type: ignore
    time: "int?" = None,  # type: ignore
) -> "string":  # type: ignore
    """
    Create the rm command required to cleanup a container.

    :param container: The container that should be removed.
    :param force: Force removal of a running or unusable container
    :param ignore: Ignore errors when a specified container is missing
    :param cidfile: Read the container ID from the file
    :param time: Seconds to wait for stop before killing the container
    """
    cmd: list[typing.Optional[str]] = [
        "/usr/bin/podman",
        "container",
        "rm",
        option("cidfile", cidfile),
        "--force" if force else None,
        "--ignore" if ignore else None,
        option("time", time),
        *extra_args("podman-rm", container.extra_args),
        container.name if cidfile is None else None,
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def container_run(
    container: "podman::Container",  # type: ignore
    *,
    cidfile: "string?" = None,  # type: ignore
    cgroups: "string?" = None,  # type: ignore
    pod_id_file: "string?" = None,  # type: ignore
    sdnotify: "string?" = None,  # type: ignore
    detach: "bool" = False,
    replace: "bool" = False,
) -> "string":  # type: ignore
    """
    Create the run command required to start the given container.

    :param container: The container that should be started.
    :param cidfile: Write the container ID to the file
    :param cgroups: control container cgroup configuration ("enabled"|"disabled"|"no-conmon"|"split")
    :param pod_id_file: Read the pod ID from the file
    :param sdnotify: control sd-notify behavior ("container"|"conmon"|"ignore")
    :param detach: Run container in background and print container ID
    :param replace: If a container with the same name exists, replace it
    """
    cmd: list[typing.Optional[str]] = [
        "/usr/bin/podman",
        "container",
        "run",
        option("cidfile", cidfile),
        option("cgroups", cgroups),
        option("pod-id-file", pod_id_file),
        option("sdnotify", sdnotify),
        "--detach" if detach else None,
        "--replace" if replace else None,
        *options("network", container.networks),
        *options("publish", container.publish),
        *options("add-host", container.hosts),
        "--no-hosts" if container.no_hosts else None,
        option("hostname", container.hostname),
        *{f"--label={k}={v}" for k, v in container.labels.items()},
        *options("uidmap", container.uidmap),
        *options("gidmap", container.gidmap),
        option("userns", container.userns),
        f"--name={container.name}",
        *options("volume", container.volumes),
        *[f"--env={k}={v}" for k, v in container.env.items()],
        option("env-file", container.env_file),
        option("entrypoint", container.entrypoint),
        option("user", container.user),
        *extra_args("podman-run", container.extra_args),
        container.image,
        container.command,
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def container_stop(
    container: "podman::Container",  # type: ignore
    *,
    ignore: "bool" = False,
    cidfile: "string?" = None,  # type: ignore
    time: "int?" = None,  # type: ignore
) -> "string":  # type: ignore
    """
    Create the stop command required to stop a container.

    :param container: The container that should be stopped.
    :param ignore: Ignore errors when a specified container is missing
    :param cidfile: Read the container ID from the file
    :param time: Seconds to wait for stop before killing the container
    """
    cmd: list[typing.Optional[str]] = [
        "/usr/bin/podman",
        "container",
        "stop",
        option("cidfile", cidfile),
        "--ignore" if ignore else None,
        option("time", time),
        *extra_args("podman-stop", container.extra_args),
        container.name if cidfile is None else None,
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def pod_create(
    pod: "podman::Pod",  # type: ignore
    *,
    infra_conmon_pidfile: "string?" = None,  # type: ignore
    pod_id_file: "string?" = None,  # type: ignore
    exit_policy: "string?" = None,  # type: ignore
    replace: "bool" = False,
) -> "string":  # type: ignore
    """
    Create the create command required to create the given pod.

    :param pod: The pod that should be created.
    :param infra_conmon_pidfile: Path to the file that will receive the PID of conmon
    :param pod_id_file: Read the pod ID from the file
    :param exit_policy: Behaviour when the last container exits
    :param replace: If a pod with the same name exists, replace it
    """
    cmd: list[typing.Optional[str]] = [
        "/usr/bin/podman",
        "pod",
        "create",
        option("infra-conmon-pidfile", infra_conmon_pidfile),
        option("pod-id-file", pod_id_file),
        option("exit-policy", exit_policy),
        "--replace" if replace else None,
        *options("network", pod.networks),
        *options("publish", pod.publish),
        *options("add-host", pod.hosts),
        "--no-hosts" if pod.no_hosts else None,
        option("hostname", pod.hostname),
        *{f"--label={k}={v}" for k, v in pod.labels.items()},
        *options("uidmap", pod.uidmap),
        *options("gidmap", pod.gidmap),
        option("userns", pod.userns),
        *extra_args("podman-pod-create", pod.extra_args),
        f"--name={pod.name}",
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def pod_rm(
    pod: "podman::Pod",  # type: ignore
    *,
    force: "bool" = False,
    ignore: "bool" = False,
    pod_id_file: "string?" = None,  # type: ignore
    time: "int?" = None,  # type: ignore
) -> "string":  # type: ignore
    """
    Create the rm command required to cleanup a pod.

    :param pod: The pod that should be removed.
    :param force: Force removal of a running pod by first stopping all containers,
        then removing all containers in the pod.
    :param ignore: Ignore errors when a specified pod is missing
    :param pod_id_file: Read the pod ID from the file
    :param time: Seconds to wait for stop before killing the pod
    """
    cmd: list[typing.Optional[str]] = [
        "/usr/bin/podman",
        "pod",
        "rm",
        option("pod-id-file", pod_id_file),
        "--force" if force else None,
        "--ignore" if ignore else None,
        option("time", time),
        *extra_args("podman-pod-rm", pod.extra_args),
        pod.name if pod_id_file is None else None,
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def pod_start(
    pod: "podman::Pod",  # type: ignore
    *,
    pod_id_file: "string?" = None,  # type: ignore
) -> "string":  # type: ignore
    """
    Create the start command required to start a pod.

    :param pod: The pod that should be started.
    :param pod_id_file: Read the pod ID from the file
    """
    cmd: list[typing.Optional[str]] = [
        "/usr/bin/podman",
        "pod",
        "start",
        option("pod-id-file", pod_id_file),
        *extra_args("podman-pod-start", pod.extra_args),
        pod.name if pod_id_file is None else None,
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def pod_stop(
    pod: "podman::Pod",  # type: ignore
    *,
    ignore: "bool" = False,
    pod_id_file: "string?" = None,  # type: ignore
    time: "int?" = None,  # type: ignore
) -> "string":  # type: ignore
    """
    Create the stop command required to stop a pod.

    :param pod: The pod that should be stopped.
    :param ignore: Ignore errors when a specified pod is missing
    :param pod_id_file: Read the pod ID from the file
    :param time: Seconds to wait for stop before killing the pod
    """
    cmd: list[typing.Optional[str]] = [
        "/usr/bin/podman",
        "pod",
        "stop",
        option("pod-id-file", pod_id_file),
        "--ignore" if ignore else None,
        option("time", time),
        *extra_args("podman-pod-stop", pod.extra_args),
        pod.name if pod_id_file is None else None,
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def auto_update(auto_update: "podman::AutoUpdate") -> "string":  # type: ignore
    """
    Create the podman auto-update command for the given auto update entity.
    """
    cmd: list[str | None] = [
        "/usr/bin/podman",
        "auto-update",
        option("authfile", auto_update.authfile),
        option("rollback", auto_update.rollback),
        option("tls-verify", auto_update.tls_verify),
    ]
    return " ".join(i for i in cmd if i is not None)
