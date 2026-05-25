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

import pathlib

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
            env_file="/etc/postgres.env",
            environment_host=true,
            entrypoint="/usr/local/bin/docker-entrypoint.sh",
            command="postgres",
            user="postgres:postgres",
            group="postgres",
            group_add=["wheel"],
            working_dir="/var/lib/postgresql",
            hostname="db.local",
            labels={{"role": "database"}},
            annotations={{"io.kubernetes.cri-o.image": "postgres"}},
            no_hosts=true,
            userns="keep-id",
            sub_uid_map="containers",
            sub_gid_map="containers",
            podman_args=["--rm"],
            global_args=["--log-level=debug"],
            containers_conf_module=["/etc/containers/containers-extra.conf"],
            dns=["1.1.1.1", "8.8.8.8"],
            dns_search=["example.com"],
            dns_option=["ndots:1"],
            network_alias=["db"],
            ip="172.42.0.2",
            ip6="fd00::2",
            shm_size="128m",
            expose_host_port=["5432"],
            volumes=[
                Volume(
                    source="/tmp/pgdata",
                    container_dir="/var/lib/postgresql/data",
                    options=["z"],
                ),
            ],
            mount=["type=tmpfs,destination=/run/postgres"],
            tmpfs=["/run/postgres-tmp:rw,size=64m"],
            read_only=true,
            read_only_tmpfs=true,
            add_device=["/dev/null:/dev/null:rwm"],
            add_capability=["NET_ADMIN"],
            drop_capability=["AUDIT_WRITE"],
            memory="512m",
            pids_limit=2048,
            ulimit=["nofile=1000:1000"],
            cgroups_mode="enabled",
            log_driver="journald",
            log_opt=["tag=postgres"],
            pull="missing",
            run_init=true,
            stop_signal="SIGTERM",
            stop_timeout=30,
            timezone="UTC",
            health=Health(
                cmd="pg_isready",
                interval="30s",
                retries=3,
                timeout="5s",
                start_period="10s",
                startup_cmd="pg_isready -t 1",
                startup_interval="5s",
                startup_retries=10,
                startup_success=1,
                startup_timeout="2s",
                log_destination="local",
                max_log_count=5,
                max_log_size=500,
                on_failure="restart",
            ),
            notify="healthy",
            auto_update="registry",
            security_label=SecurityLabel(
                disable=false,
                type="container_t",
                level="s0:c1,c2",
                file_type="container_file_t",
                nested=false,
            ),
            seccomp_profile="/etc/containers/seccomp.json",
            mask="/proc/kcore",
            unmask="/sys/fs/cgroup",
            no_new_privileges=true,
            sysctl={{"net.ipv4.ip_unprivileged_port_start": "0"}},
            http_proxy=true,
            retry=3,
            retry_delay="2s",
            hosts=[
                Host(host="db.local", ip="127.0.0.1"),
            ],
            publish=[
                Publish(host_port="5432", container_port="5432"),
            ],
            extra_args=[
                ExtraArg(name="cidfile", value="/tmp/cid", cmd="podman-run"),
            ],
        )

        podman::services::SystemdContainer(
            container=db,
            state={repr(state)},
            enabled=true,
            systemd_unit_dir="/tmp/systemd/user",
            systemctl_command=["systemctl", "--user"],
        )
    """

    project.compile(model, no_dedent=False)


def test_all_options_in_command(project: Project) -> None:
    """
    Compile the model and verify each Container option is rendered into the
    generated systemd unit file (via the podman::container_run cli command).
    """
    test_model(project, state="stopped")

    container_unit_file_path = (
        pathlib.Path("/tmp/systemd/user") / "container-postgresql-server.service"
    )
    unit_file_resource = next(
        r
        for r in project.resources.values()
        if getattr(r, "path", None) == str(container_unit_file_path)
    )
    content = unit_file_resource.content

    # cgroups_mode and notify are overridden by SystemdContainer's wrapper
    # (cgroups=no-conmon, sdnotify=conmon).  They are exercised by the
    # quadlet variant test.
    expected = [
        "--module=/etc/containers/containers-extra.conf",
        "--log-level=debug",
        "container run",
        "--network=test-net:ip=172.42.0.2",
        "--network-alias=db",
        "--publish=5432:5432",
        "--expose=5432",
        "--add-host=db.local:127.0.0.1",
        "--no-hosts",
        "--hostname=db.local",
        "--ip=172.42.0.2",
        "--ip6=fd00::2",
        "--dns=1.1.1.1",
        "--dns=8.8.8.8",
        "--dns-search=example.com",
        "--dns-option=ndots:1",
        "--label=role=database",
        "--annotation=io.kubernetes.cri-o.image=postgres",
        "--uidmap=999:@1000",
        "--gidmap=999:@1000",
        "--subuidname=containers",
        "--subgidname=containers",
        "--userns=keep-id",
        "--shm-size=128m",
        "--name=postgresql-server",
        "--volume=/tmp/pgdata:/var/lib/postgresql/data:z",
        "--mount=type=tmpfs,destination=/run/postgres",
        "--tmpfs=/run/postgres-tmp:rw,size=64m",
        "--read-only",
        "--read-only-tmpfs=true",
        "--device=/dev/null:/dev/null:rwm",
        "--cap-add=NET_ADMIN",
        "--cap-drop=AUDIT_WRITE",
        "--memory=512m",
        "--pids-limit=2048",
        "--ulimit=nofile=1000:1000",
        "--log-driver=journald",
        "--log-opt=tag=postgres",
        "--pull=missing",
        "--init",
        "--stop-signal=SIGTERM",
        "--stop-timeout=30",
        "--tz=UTC",
        "--health-cmd=pg_isready",
        "--health-interval=30s",
        "--health-retries=3",
        "--health-timeout=5s",
        "--health-start-period=10s",
        "--health-startup-cmd=",
        "pg_isready -t 1",
        "--health-startup-interval=5s",
        "--health-startup-retries=10",
        "--health-startup-success=1",
        "--health-startup-timeout=2s",
        "--health-log-destination=local",
        "--health-max-log-count=5",
        "--health-max-log-size=500",
        "--health-on-failure=restart",
        "--env=POSTGRES_USER=test",
        "--env=POSTGRES_PASSWORD=test",
        "--env-file=/etc/postgres.env",
        "--env-host",
        "--entrypoint=/usr/local/bin/docker-entrypoint.sh",
        "--user=postgres:postgres",
        "--group=postgres",
        "--group-add=wheel",
        "--workdir=/var/lib/postgresql",
        "--security-opt=no-new-privileges",
        "--security-opt=label=type:container_t",
        "--security-opt=label=level:s0:c1,c2",
        "--security-opt=label=filetype:container_file_t",
        "--security-opt=seccomp=/etc/containers/seccomp.json",
        "--security-opt=mask=/proc/kcore",
        "--security-opt=unmask=/sys/fs/cgroup",
        "--sysctl=net.ipv4.ip_unprivileged_port_start=0",
        "--http-proxy=true",
        "--retry=3",
        "--retry-delay=2s",
        "--cidfile=/tmp/cid",
        "--rm",
        "docker.io/library/postgres:13",
        "postgres",
    ]
    missing = [token for token in expected if token not in content]
    assert not missing, f"missing tokens in unit file: {missing}\ncontent:\n{content}"


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
