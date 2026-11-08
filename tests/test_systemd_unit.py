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

import collections.abc
import pathlib
import shutil
import subprocess
import uuid

import pytest
from pytest_inmanta.plugin import Project, Result

from inmanta import const

UNIT = "files::SystemdUnit"
RELOAD = "files::SystemdDaemonReload"


def build_model(
    name: str,
    *,
    state: str,
    enabled: bool = True,
    command: str = "sleep infinity",
    quadlet: bool = True,
    systemd_unit_dir: str = "/tmp/systemd/user",
    systemd_container_dir: str = "/tmp/containers/systemd",
) -> str:
    return f"""
        import podman
        import podman::services
        import mitogen
        import std

        host = std::Host(
            name="localhost",
            remote_agent=true,
            ip="127.0.0.1",
            os=std::linux,
            via=mitogen::Local(),
        )

        container = podman::Container(
            host=host,
            name={name!r},
            image="docker.io/library/python:3.13-alpine",
            command={command!r},
        )

        podman::services::SystemdContainer(
            container=container,
            state={state!r},
            enabled={"true" if enabled else "false"},
            systemd_unit_dir={systemd_unit_dir!r},
            systemd_container_dir={systemd_container_dir!r},
            systemctl_command=["systemctl", "--user"],
            quadlet={"true" if quadlet else "false"},
        )
    """


@pytest.mark.parametrize(
    ("state", "enabled", "expected"),
    [
        # state, enabled -> enabled, active, purged, up_to_date
        ("running", True, (True, True, False, None)),
        ("restart", True, (True, True, False, True)),
        ("stopped", False, (False, False, False, None)),
        ("configured", True, (None, None, False, None)),
        ("configured", False, (False, None, False, None)),
        ("removed", True, (False, False, True, None)),
    ],
)
def test_model(
    project: Project,
    state: str,
    enabled: bool,
    expected: tuple[bool | None, bool | None, bool, bool | None],
) -> None:
    """
    The state of the service is the state of its main unit, which is deployed
    after its files, unless it is removed: it is then stopped first.
    """
    for quadlet in [True, False]:
        project.compile(
            build_model("app", state=state, enabled=enabled, quadlet=quadlet)
        )

        unit = project.get_resource(UNIT)
        assert unit is not None
        assert unit.id.attribute_value == "user/current/container-app.service"
        assert unit.user == "current"
        assert (
            unit.enabled,
            unit.active,
            unit.purged,
            unit.up_to_date,
        ) == expected

        unit_file = project.get_resource(
            "podman::services::QuadletUnitFile" if quadlet else "files::SystemdUnitFile"
        )
        assert unit_file is not None
        if state == "removed":
            assert unit.id in unit_file.requires
            assert unit_file.id not in unit.requires
        else:
            assert unit_file.id in unit.requires
            assert unit.id not in unit_file.requires


@pytest.fixture
def user_quadlet() -> collections.abc.Iterator[str]:
    """
    The name of a container, deployed as a quadlet of the user, removed after
    the test.
    """
    if shutil.which("podman") is None:
        pytest.skip("Podman is not installed")
    systemctl = ["systemctl", "--user"]
    # The return code doesn't distinguish a degraded manager from a missing one
    status = subprocess.run(
        [*systemctl, "is-system-running"], capture_output=True, text=True
    ).stdout.strip()
    if status not in ("running", "degraded"):
        pytest.skip("No systemd user manager to test with")

    name = f"inmanta-podman-test-{uuid.uuid4().hex[:8]}"
    yield name
    service = f"container-{name}.service"
    subprocess.run([*systemctl, "stop", "--", service])
    subprocess.run([*systemctl, "reset-failed", "--", service])
    quadlet = (
        pathlib.Path.home() / f".config/containers/systemd/container-{name}.container"
    )
    quadlet.unlink(missing_ok=True)
    subprocess.run([*systemctl, "daemon-reload"])


def show(name: str, property: str) -> str:
    return subprocess.run(
        [
            "systemctl",
            "--user",
            "show",
            "--property",
            property,
            "--value",
            "--",
            f"container-{name}.service",
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_deploy_user_quadlet(project: Project, user_quadlet: str) -> None:
    """
    Run a container as a quadlet of the user, restart it when its quadlet
    changed, and stop it before its quadlet is removed.
    """
    home = pathlib.Path.home()

    def deploy(
        state: str, enabled: bool = True, command: str = "sleep infinity"
    ) -> None:
        project.compile(
            build_model(
                user_quadlet,
                state=state,
                enabled=enabled,
                command=command,
                systemd_unit_dir=str(home / ".config/systemd/user"),
                systemd_container_dir=str(home / ".config/containers/systemd"),
            )
        )
        project.deploy_all(exclude_all=["std::AgentConfig"]).assert_all()
        Result(
            {
                r: project.dryrun(r, run_as_root=False)
                for r in project.resources.values()
                if not r.is_type("std::AgentConfig")
            }
        ).assert_has_no_changes()

    deploy("running")
    assert show(user_quadlet, "ActiveState") == "active"
    started_at = show(user_quadlet, "ActiveEnterTimestamp")

    # Nothing changed, the restart state doesn't restart the container
    deploy("restart", enabled=False)
    assert show(user_quadlet, "ActiveEnterTimestamp") == started_at

    # The quadlet changes, the restart state restarts the container
    deploy("restart", command="sleep 3600")
    assert show(user_quadlet, "ActiveState") == "active"
    assert show(user_quadlet, "ActiveEnterTimestamp") != started_at
    project.deploy_resource(UNIT, change=const.Change.nochange)

    deploy("removed")
    assert show(user_quadlet, "LoadState") == "not-found"
