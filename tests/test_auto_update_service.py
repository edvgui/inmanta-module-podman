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

from pytest_inmanta.plugin import Project, Result


def test_model(
    project: Project,
    state: str = "stopped",
    on_calendar: str | None = None,
    systemctl_command: list[str] | None = None,
    retries: int | None = None,
) -> None:
    if systemctl_command is None:
        systemctl_command = ["systemctl", "--user"]
    model = f"""
        import podman
        import podman::services
        import mitogen
        import std
        import files

        host = std::Host(
            name="localhost",
            remote_agent=true,
            ip="127.0.0.1",
            os=std::linux,
            via=mitogen::Local(),
        )

        a = podman::AutoUpdate(
            host=host,
            rollback=false,
        )

        podman::services::SystemdAutoUpdate(
            auto_update=a,
            state={repr(state)},
            enabled=true,
            systemd_unit_dir="/tmp/systemd/user",
            systemctl_command={systemctl_command!r},
            {f"on_calendar={on_calendar!r}," if on_calendar else ""}
            {f"retries={retries!r}," if retries is not None else ""}
        )
    """

    project.compile(model, no_dedent=False)


def test_deploy(project: Project) -> None:
    # Go over all the supported state, and make sure the resource can
    # be deployed
    for state in ["configured", "stopped", "removed"]:
        # Compile the model
        test_model(project, state=state)

        # Deploy all the resources
        project.deploy_all(
            exclude_all=[
                "std::AgentConfig",
                "files::SystemdUnit",
                "files::SystemdDaemonReload",
            ],
        ).assert_all()

        # Assert that the desired state is stable
        dry_run_result = Result(
            {
                r: project.dryrun(r, run_as_root=False)
                for r in project.resources.values()
                if (
                    not r.is_type("std::AgentConfig")
                    and not r.is_type("files::SystemdUnit")
                    and not r.is_type("files::SystemdDaemonReload")
                )
            }
        )
        dry_run_result.assert_has_no_changes()


def _unit_content(project: Project, name: str) -> str:
    """
    Return the content of the generated unit file with the given name.
    """
    path = f"/tmp/systemd/user/{name}"
    return next(
        r for r in project.resources.values() if getattr(r, "path", None) == path
    ).content


def test_waits_for_the_network(project: Project) -> None:
    """
    The auto-update needs the registries: it waits for the network to be
    online, through podman's user unit for a user manager, which can't see
    network-online.target.
    """
    test_model(project)
    content = _unit_content(project, "podman-auto-update.service")
    assert "Wants=podman-user-wait-network-online.service" in content
    assert "After=podman-user-wait-network-online.service" in content
    assert "network-online.service" not in content.replace(
        "podman-user-wait-network-online.service", ""
    )

    test_model(project, systemctl_command=["systemctl"])
    content = _unit_content(project, "podman-auto-update.service")
    assert "Wants=network-online.target" in content
    assert "After=network-online.target" in content


def test_timer_does_not_start_the_service(project: Project) -> None:
    """
    The timer only triggers the service on its calendar: it doesn't require
    it, or starting the timer (at boot, or on a deploy) would also run it.
    """
    test_model(project, on_calendar="*-*-* 03:00:00")
    timer = _unit_content(project, "podman-auto-update.timer")
    assert "Requires=" not in timer
    assert "Unit=podman-auto-update.service" in timer
    assert "OnCalendar=*-*-* 03:00:00" in timer


def test_retries_on_failure(project: Project) -> None:
    """
    A failed image check (e.g. a registry timeout or rate limit) fails the
    whole run: it is run again later, and the on_failure units only trigger
    once the retries are exhausted.  The prune of the replaced images runs
    whether the run fails or not.
    """
    test_model(project)
    content = _unit_content(project, "podman-auto-update.service")
    assert "Restart=on-failure" in content
    assert "RestartSec=600" in content
    assert "RestartMode=direct" in content
    assert "StartLimitBurst=3" in content
    assert "StartLimitIntervalSec=12600" in content
    assert "ExecStopPost=/usr/bin/podman image prune -f" in content
    assert "ExecStartPost=" not in content


def test_no_retries(project: Project) -> None:
    """
    With retries=0, a failed run isn't run again.
    """
    test_model(project, retries=0)
    content = _unit_content(project, "podman-auto-update.service")
    for directive in ["Restart=", "RestartSec=", "RestartMode=", "StartLimit"]:
        assert directive not in content
    assert "ExecStopPost=/usr/bin/podman image prune -f" in content
