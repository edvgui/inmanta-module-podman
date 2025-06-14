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
    project: Project, state: str = "stopped", on_calendar: str | None = None
) -> None:
    model = f"""
        import podman
        import podman::container_like
        import podman::container
        import podman::services
        import std
        import mitogen
        import files

        host = std::Host(
            name="localhost",
            remote_agent=true,
            ip="127.0.0.1",
            os=std::linux,
            via=mitogen::Local(),
        )

        pod = podman::Pod(
            host=host,
            name="inmanta-orchestrator",
            hostname=pod.name,
            networks=[
                BridgeNetwork(
                    name="test-net",
                    ip=std::ipindex("172.42.0.0/24", position=3),
                ),
            ],
            publish=[
                Publish(
                    host_port="127.0.0.1:8888",
                    container_port="8888",
                ),
            ],
            uidmap=[
                IdMap(container_id="993", host_id="@1000"),
            ],
            gidmap=[
                IdMap(container_id="993", host_id="@1000"),
            ],
            containers=[
                podman::Container(
                    host=host,
                    name=f"{{pod.name}}-server",
                    image="ghcr.io/inmanta/orchestrator:latest",
                    user="993:993",
                    entrypoint="/usr/bin/inmanta",
                    command="-vvv --timed-logs server",
                ),
            ],
        )

        podman::services::SystemdPod(
            pod=pod,
            state={repr(state)},
            on_calendar={repr(on_calendar) if on_calendar is not None else "null"},
            enabled=true,
            systemd_unit_dir="/tmp/systemd/user",
            systemctl_command=["systemctl", "--user"],
        )
    """

    project.compile(model, no_dedent=False)


def test_deploy(project: Project) -> None:
    # Go over all the supported state, and make sure the resource can
    # be deployed
    for on_calendar in [None, "*-*-* *:*:00"]:
        for state in ["configured", "stopped", "removed"]:
            # Compile the model
            test_model(project, state=state, on_calendar=on_calendar)

            # Deploy all the resources
            project.deploy_all(
                exclude_all=[
                    "std::AgentConfig",
                    "exec::Run",
                ],
            ).assert_all()

            # Assert that the desired state is stable
            dry_run_result = Result(
                {
                    r: project.dryrun(r, run_as_root=False)
                    for r in project.resources.values()
                    if (
                        not r.is_type("std::AgentConfig") and not r.is_type("exec::Run")
                    )
                }
            )
            dry_run_result.assert_has_no_changes()
