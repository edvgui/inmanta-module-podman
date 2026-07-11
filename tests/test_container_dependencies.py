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

import pathlib

from pytest_inmanta.plugin import Project, Result


def build_model(
    *,
    quadlet: bool = False,
    on_calendar: str | None = None,
    state: str = "stopped",
) -> str:
    """
    Build a model where an ``app`` container depends on a ``db`` container.

    :param quadlet: Whether the services should be generated as quadlet units.
    :param on_calendar: When set, the dependent service is calendar-triggered
        (like a periodic database dump) instead of being long-running.
    :param state: The desired state for the services.
    """
    container_dir = (
        'systemd_container_dir="/tmp/containers/systemd",' if quadlet else ""
    )
    on_calendar_option = (
        f"on_calendar={on_calendar!r}," if on_calendar is not None else ""
    )
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

        db = podman::Container(
            host=host,
            name="postgresql-server",
            image="docker.io/library/postgres:13",
        )

        app = podman::Container(
            host=host,
            name="my-app",
            image="docker.io/library/nginx:latest",
        )

        db_service = podman::services::SystemdContainer(
            container=db,
            state={state!r},
            systemd_unit_dir="/tmp/systemd/user",
            {container_dir}
            systemctl_command=["systemctl", "--user"],
            quadlet={"true" if quadlet else "false"},
        )

        podman::services::SystemdContainer(
            container=app,
            state={state!r},
            {on_calendar_option}
            systemd_unit_dir="/tmp/systemd/user",
            {container_dir}
            systemctl_command=["systemctl", "--user"],
            quadlet={"true" if quadlet else "false"},
            dependencies=[db_service],
        )
    """


def _dependent_unit_content(project: Project, *, quadlet: bool) -> str:
    """
    Return the content of the generated unit file for the ``app`` container.
    """
    if quadlet:
        path = pathlib.Path("/tmp/containers/systemd") / "container-my-app.container"
    else:
        path = pathlib.Path("/tmp/systemd/user") / "container-my-app.service"

    unit_file_resource = next(
        r for r in project.resources.values() if getattr(r, "path", None) == str(path)
    )
    return unit_file_resource.content


def test_dependency_in_service_unit(project: Project) -> None:
    """
    A long-running container that depends on another one must reference it with
    both a ``Requires=`` and an ``After=`` directive in its unit file.
    """
    project.compile(build_model(), no_dedent=False)

    content = _dependent_unit_content(project, quadlet=False)
    assert "Requires=container-postgresql-server.service" in content
    assert "After=container-postgresql-server.service" in content


def test_dependency_in_quadlet_unit(project: Project) -> None:
    """
    Same as above, but for a container managed through a quadlet unit file.
    """
    project.compile(build_model(quadlet=True), no_dedent=False)

    content = _dependent_unit_content(project, quadlet=True)
    assert "Requires=container-postgresql-server.service" in content
    assert "After=container-postgresql-server.service" in content


def test_dependency_on_calendar_service(project: Project) -> None:
    """
    A calendar-triggered container (e.g. a periodic database dump) that depends
    on another container must still pull in its dependency via ``Requires=`` and
    ``After=`` so the dependency is running when the timer activates the service.
    """
    project.compile(build_model(on_calendar="daily"), no_dedent=False)

    content = _dependent_unit_content(project, quadlet=False)
    assert "Requires=container-postgresql-server.service" in content
    assert "After=container-postgresql-server.service" in content


def test_no_dependency_no_directive(project: Project) -> None:
    """
    A container without dependencies must not gain a ``Requires=`` directive
    pointing at another container.
    """
    project.compile(
        """
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

        app = podman::Container(
            host=host,
            name="my-app",
            image="docker.io/library/nginx:latest",
        )

        podman::services::SystemdContainer(
            container=app,
            state="stopped",
            systemd_unit_dir="/tmp/systemd/user",
            systemctl_command=["systemctl", "--user"],
        )
        """,
        no_dedent=False,
    )

    content = _dependent_unit_content(project, quadlet=False)
    assert "Requires=container-" not in content


def test_multiple_dependencies(project: Project) -> None:
    """
    A container can depend on several other services at once.
    """
    project.compile(
        """
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

        db = podman::Container(host=host, name="database", image="postgres:13")
        cache = podman::Container(host=host, name="cache", image="redis:7")
        app = podman::Container(host=host, name="my-app", image="nginx:latest")

        db_service = podman::services::SystemdContainer(
            container=db,
            state="stopped",
            systemd_unit_dir="/tmp/systemd/user",
            systemctl_command=["systemctl", "--user"],
        )
        cache_service = podman::services::SystemdContainer(
            container=cache,
            state="stopped",
            systemd_unit_dir="/tmp/systemd/user",
            systemctl_command=["systemctl", "--user"],
        )

        podman::services::SystemdContainer(
            container=app,
            state="stopped",
            systemd_unit_dir="/tmp/systemd/user",
            systemctl_command=["systemctl", "--user"],
            dependencies=[db_service, cache_service],
        )
        """,
        no_dedent=False,
    )

    content = _dependent_unit_content(project, quadlet=False)
    assert "Requires=container-database.service" in content
    assert "After=container-database.service" in content
    assert "Requires=container-cache.service" in content
    assert "After=container-cache.service" in content


def test_deploy_with_dependencies(project: Project) -> None:
    """
    Make sure a model using container dependencies can be deployed and reaches
    a stable state, across the supported service states.
    """
    for state in ["configured", "stopped", "removed"]:
        project.compile(build_model(state=state), no_dedent=False)

        project.deploy_all(
            exclude_all=[
                "std::AgentConfig",
                "exec::Run",
            ],
        ).assert_all()

        dry_run_result = Result(
            {
                r: project.dryrun(r, run_as_root=False)
                for r in project.resources.values()
                if (not r.is_type("std::AgentConfig") and not r.is_type("exec::Run"))
            }
        )
        dry_run_result.assert_has_no_changes()
