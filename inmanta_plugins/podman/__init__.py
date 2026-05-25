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

import shlex
import typing

import inmanta.plugins


@inmanta.plugins.plugin()
def removesuffix(s: str, suffix: str) -> str:
    """
    Remove the given suffix from the input string.

    :param s: The string that should remove the suffix from.
    :param suffix: The suffix to remove from the string, if it has it.
    """
    return s.removesuffix(suffix)


@inmanta.plugins.plugin()
def shlex_join(cmd: list[str]) -> str:
    """
    Join all the parts of the command into a string that can safely be parsed
    by a shell as a valid command.

    :param cmd: All the parts of the command
    """
    return shlex.join(cmd)


@inmanta.plugins.plugin()
def inline_options(options: dict) -> str:
    """
    Convert a dict of options into a comma-separated list of key=value pairs.

    :param options: The options dict to serialize into a string.
    """
    return ",".join(f"{k}={v}" for k, v in options.items() if v is not None)


@inmanta.plugins.plugin()
def join(parts: list[str], *, separator: str) -> str:
    """
    Join all the elements in the list together, use the separator in
    between each joined part.

    :param parts: The list of string we want to join
    :param separator: The separator to use in the join
    """
    return separator.join(parts)


def option(name: str, value: str | int | bool | None) -> str | None:
    """
    Helper function to create a cli option with the given name and value,
    or None if the value is None.  Booleans are formatted as ``true``/``false``.

    :param name: The name of the cli option
    :param value: The value of the cli option
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return f"--{name}={'true' if value else 'false'}"
    return f"--{name}={value}"


def flag(name: str, value: bool | None) -> str | None:
    """
    Helper to emit a boolean cli flag when value is true.

    :param name: The name of the cli flag
    :param value: The value of the cli flag (or None to omit)
    """
    return f"--{name}" if value else None


def options(name: str, values: typing.Sequence[object]) -> typing.Sequence[str]:
    """
    Helper function to a repeating cli option, based on the given sequence
    of objects.  The provided object should have the `cli_option` attribute,
    providing the value for the option.

    :param name: The name of the cli option
    :param values: The list of objects
    """
    return [f"--{name}={value.cli_option}" for value in values]


def repeated(name: str, values: typing.Sequence[str]) -> typing.Sequence[str]:
    """
    Helper function to emit a repeating cli option, based on a sequence of strings.

    :param name: The name of the cli option
    :param values: The list of values for the option
    """
    return [f"--{name}={value}" for value in values]


def health_options(health: object | None) -> typing.Sequence[str]:
    """
    Helper function to serialize the healthcheck options into the cli arguments
    expected by the podman cli.

    :param health: A ``podman::container::Health`` entity, or None.
    """
    if health is None:
        return []
    return [
        opt
        for opt in [
            option("health-cmd", health.cmd),
            option("health-interval", health.interval),
            option("health-retries", health.retries),
            option("health-timeout", health.timeout),
            option("health-start-period", health.start_period),
            option("health-startup-cmd", health.startup_cmd),
            option("health-startup-interval", health.startup_interval),
            option("health-startup-retries", health.startup_retries),
            option("health-startup-success", health.startup_success),
            option("health-startup-timeout", health.startup_timeout),
            option("health-log-destination", health.log_destination),
            option("health-max-log-count", health.max_log_count),
            option("health-max-log-size", health.max_log_size),
            option("health-on-failure", health.on_failure),
        ]
        if opt is not None
    ]


def security_label_options(label: object | None) -> typing.Sequence[str]:
    """
    Helper function to serialize the security label options into the cli
    arguments expected by the podman cli.  Each option is emitted as a
    ``--security-opt`` argument.

    :param label: A ``podman::container::SecurityLabel`` entity, or None.
    """
    if label is None:
        return []
    parts: list[str | None] = [
        "label=disable" if label.disable else None,
        f"label=type:{label.type}" if label.type is not None else None,
        f"label=level:{label.level}" if label.level is not None else None,
        f"label=filetype:{label.file_type}" if label.file_type is not None else None,
        "label=nested" if label.nested else None,
    ]
    return [f"--security-opt={part}" for part in parts if part is not None]


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
    container: typing.Annotated[
        typing.Any, inmanta.plugins.ModelType["podman::Container"]
    ],
    *,
    force: bool = False,
    ignore: bool = False,
    cidfile: str | None = None,
    time: int | None = None,
) -> str:
    """
    Create the rm command required to cleanup a container.

    :param container: The container that should be removed.
    :param force: Force removal of a running or unusable container
    :param ignore: Ignore errors when a specified container is missing
    :param cidfile: Read the container ID from the file
    :param time: Seconds to wait for stop before killing the container
    """
    cmd: list[str | None] = [
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
    container: typing.Annotated[
        typing.Any, inmanta.plugins.ModelType["podman::Container"]
    ],
    *,
    cidfile: str | None = None,
    cgroups: str | None = None,
    pod_id_file: str | None = None,
    sdnotify: str | None = None,
    detach: bool = False,
    replace: bool = False,
) -> str:
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
    cmd: list[str | None] = [
        "/usr/bin/podman",
        *repeated("module", container.containers_conf_module),
        *container.global_args,
        "container",
        "run",
        option("cidfile", cidfile),
        option("cgroups", cgroups or container.cgroups_mode),
        option("pod-id-file", pod_id_file),
        option("sdnotify", sdnotify or container.notify),
        flag("detach", detach),
        flag("replace", replace),
        *options("network", container.networks),
        *repeated("network-alias", container.network_alias),
        *options("publish", container.publish),
        *repeated("expose", container.expose_host_port),
        *options("add-host", container.hosts),
        flag("no-hosts", container.no_hosts),
        option("hostname", container.hostname),
        option("ip", container.ip),
        option("ip6", container.ip6),
        *repeated("dns", container.dns),
        *repeated("dns-search", container.dns_search),
        *repeated("dns-option", container.dns_option),
        *{f"--label={k}={v}" for k, v in container.labels.items()},
        *(f"--annotation={k}={v}" for k, v in container.annotations.items()),
        *options("uidmap", container.uidmap),
        *options("gidmap", container.gidmap),
        option("subuidname", container.sub_uid_map),
        option("subgidname", container.sub_gid_map),
        option("userns", container.userns),
        option("shm-size", container.shm_size),
        f"--name={container.name}",
        *options("volume", container.volumes),
        *repeated("mount", container.mount),
        *repeated("tmpfs", container.tmpfs),
        flag("read-only", container.read_only),
        option("read-only-tmpfs", container.read_only_tmpfs),
        *repeated("device", container.add_device),
        *repeated("cap-add", container.add_capability),
        *repeated("cap-drop", container.drop_capability),
        option("memory", container.memory),
        option("pids-limit", container.pids_limit),
        *repeated("ulimit", container.ulimit),
        option("log-driver", container.log_driver),
        *repeated("log-opt", container.log_opt),
        option("pull", container.pull),
        flag("init", container.run_init),
        option("stop-signal", container.stop_signal),
        option("stop-timeout", container.stop_timeout),
        option("tz", container.timezone),
        *health_options(container.health),
        *[f"--env={k}={v}" for k, v in container.env.items()],
        option("env-file", container.env_file),
        flag("env-host", container.environment_host),
        option("entrypoint", container.entrypoint),
        option("user", container.user),
        option("group", container.group),
        *repeated("group-add", container.group_add),
        option("workdir", container.working_dir),
        option(
            "security-opt", "no-new-privileges" if container.no_new_privileges else None
        ),
        *security_label_options(container.security_label),
        option(
            "security-opt",
            (
                f"seccomp={container.seccomp_profile}"
                if container.seccomp_profile is not None
                else None
            ),
        ),
        option(
            "security-opt",
            f"mask={container.mask}" if container.mask is not None else None,
        ),
        option(
            "security-opt",
            f"unmask={container.unmask}" if container.unmask is not None else None,
        ),
        *[f"--sysctl={k}={v}" for k, v in container.sysctl.items()],
        option("rootfs", container.rootfs),
        option("http-proxy", container.http_proxy),
        option("retry", container.retry),
        option("retry-delay", container.retry_delay),
        *extra_args("podman-run", container.extra_args),
        *container.podman_args,
        container.image,
        container.command,
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def container_stop(
    container: typing.Annotated[
        typing.Any, inmanta.plugins.ModelType["podman::Container"]
    ],
    *,
    ignore: bool = False,
    cidfile: str | None = None,
    time: int | None = None,
) -> str:
    """
    Create the stop command required to stop a container.

    :param container: The container that should be stopped.
    :param ignore: Ignore errors when a specified container is missing
    :param cidfile: Read the container ID from the file
    :param time: Seconds to wait for stop before killing the container
    """
    cmd: list[str | None] = [
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
    pod: typing.Annotated[typing.Any, inmanta.plugins.ModelType["podman::Pod"]],
    *,
    infra_conmon_pidfile: str | None = None,
    pod_id_file: str | None = None,
    exit_policy: str | None = None,
    replace: bool = False,
) -> str:
    """
    Create the create command required to create the given pod.

    :param pod: The pod that should be created.
    :param infra_conmon_pidfile: Path to the file that will receive the PID of conmon
    :param pod_id_file: Read the pod ID from the file
    :param exit_policy: Behaviour when the last container exits
    :param replace: If a pod with the same name exists, replace it
    """
    cmd: list[str | None] = [
        "/usr/bin/podman",
        *repeated("module", pod.containers_conf_module),
        *pod.global_args,
        "pod",
        "create",
        option("infra-conmon-pidfile", infra_conmon_pidfile),
        option("pod-id-file", pod_id_file),
        option("exit-policy", exit_policy or pod.exit_policy),
        flag("replace", replace),
        *options("network", pod.networks),
        *repeated("network-alias", pod.network_alias),
        *options("publish", pod.publish),
        *options("add-host", pod.hosts),
        flag("no-hosts", pod.no_hosts),
        option("hostname", pod.hostname),
        option("ip", pod.ip),
        option("ip6", pod.ip6),
        *repeated("dns", pod.dns),
        *repeated("dns-search", pod.dns_search),
        *repeated("dns-option", pod.dns_option),
        option("shm-size", pod.shm_size),
        *{f"--label={k}={v}" for k, v in pod.labels.items()},
        *options("uidmap", pod.uidmap),
        *options("gidmap", pod.gidmap),
        option("subuidname", pod.sub_uid_map),
        option("subgidname", pod.sub_gid_map),
        option("userns", pod.userns),
        *options("volume", pod.volumes),
        *extra_args("podman-pod-create", pod.extra_args),
        *pod.podman_args,
        f"--name={pod.name}",
    ]
    return " ".join(i for i in cmd if i is not None)


@inmanta.plugins.plugin()
def pod_rm(
    pod: typing.Annotated[typing.Any, inmanta.plugins.ModelType["podman::Pod"]],
    *,
    force: bool = False,
    ignore: bool = False,
    pod_id_file: str | None = None,
    time: int | None = None,
) -> str:
    """
    Create the rm command required to cleanup a pod.

    :param pod: The pod that should be removed.
    :param force: Force removal of a running pod by first stopping all containers,
        then removing all containers in the pod.
    :param ignore: Ignore errors when a specified pod is missing
    :param pod_id_file: Read the pod ID from the file
    :param time: Seconds to wait for stop before killing the pod
    """
    cmd: list[str | None] = [
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
    pod: typing.Annotated[typing.Any, inmanta.plugins.ModelType["podman::Pod"]],
    *,
    pod_id_file: str | None = None,
) -> str:
    """
    Create the start command required to start a pod.

    :param pod: The pod that should be started.
    :param pod_id_file: Read the pod ID from the file
    """
    cmd: list[str | None] = [
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
    pod: typing.Annotated[typing.Any, inmanta.plugins.ModelType["podman::Pod"]],
    *,
    ignore: bool = False,
    pod_id_file: str | None = None,
    time: int | None = None,
) -> str:
    """
    Create the stop command required to stop a pod.

    :param pod: The pod that should be stopped.
    :param ignore: Ignore errors when a specified pod is missing
    :param pod_id_file: Read the pod ID from the file
    :param time: Seconds to wait for stop before killing the pod
    """
    cmd: list[str | None] = [
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
def auto_update(
    auto_update: typing.Annotated[
        typing.Any, inmanta.plugins.ModelType["podman::AutoUpdate"]
    ],
) -> str:
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
