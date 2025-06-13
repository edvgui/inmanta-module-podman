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


def test_model(project: Project, state: str = "stopped") -> None:
    model = f"""
        import podman
        import podman::container_like
        import podman::container
        import podman::services
        import mitogen
        import std
        import files

        user = std::get_env("USER")

        host = std::Host(
            name="localhost",
            remote_agent=true,
            remote_user=user,
            ip="127.0.0.1",
            os=std::linux,
            via=mitogen::Local(),
        )

        db = podman::Container(
            host=host,
            name="postgresql-server",
            image="docker.io/library/postgres:13",
            owner=user,
            networks=[
                BridgeNetwork(
                    name="test-net",
                    ip=std::ipindex("172.42.0.0/24", position=2),
                ),
            ],
            uidmap=[
                IdMap(container_id="999", host_id="@1000"),
            ],
            gidmap=[
                IdMap(container_id="999", host_id="@1000"),
            ],
            env={{
                "POSTGRES_USER": "test",
                "POSTGRES_PASSWORD": "test",
            }},
            volumes=[
                Volume(
                    source="/tmp/pgdata",
                    container_dir="/var/lib/postgresql/data",
                    options=["z"],
                ),
            ],
        )

        podman::services::SystemdContainer(
            container=db,
            state={repr(state)},
            enabled=true,
            systemd_unit_dir=files::path_join("/home", user, ".config/systemd/user"),
            systemd_container_dir=files::path_join("/home", user, ".config/containers/systemd"),
            systemctl_command=["systemctl", "--user"],
            quadlet=true,
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
                "exec::Run",
            ],
        ).assert_all()

        # Assert that the desired state is stable
        dry_run_result = Result(
            {
                r: project.dryrun(r, run_as_root=False)
                for r in project.resources.values()
                if (not r.is_type("std::AgentConfig") and not r.is_type("exec::Run"))
            }
        )
        dry_run_result.assert_has_no_changes()
