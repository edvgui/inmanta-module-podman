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
            systemd_container_dir="/tmp/containers/systemd",
            systemctl_command=["systemctl", "--user"],
            quadlet=true,
        )
    """

    project.compile(model, no_dedent=False)


def test_all_options_in_template(project: Project) -> None:
    """
    Compile the model and verify each Container option is rendered into the
    generated quadlet unit file.
    """
    test_model(project, state="stopped")

    # Find the systemd unit file resource and read its content
    container_unit_file_path = (
        pathlib.Path("/tmp/containers/systemd")
        / "container-postgresql-server.container"
    )
    unit_file_resource = next(
        r
        for r in project.resources.values()
        if getattr(r, "path", None) == str(container_unit_file_path)
    )
    content = unit_file_resource.content

    expected = [
        "[Container]",
        "ContainerName=postgresql-server",
        "Image=docker.io/library/postgres:13",
        "HostName=db.local",
        "Label=role=database",
        "Annotation=io.kubernetes.cri-o.image=postgres",
        "UserNS=keep-id",
        "SubUIDMap=containers",
        "SubGIDMap=containers",
        "ContainersConfModule=/etc/containers/containers-extra.conf",
        "GlobalArgs=",
        "--log-level=debug",
        "DNS=1.1.1.1",
        "DNS=8.8.8.8",
        "DNSSearch=example.com",
        "DNSOption=ndots:1",
        "IP=172.42.0.2",
        "IP6=fd00::2",
        "ShmSize=128m",
        "Environment=",
        "POSTGRES_USER=test",
        "POSTGRES_PASSWORD=test",
        "EnvironmentFile=/etc/postgres.env",
        "EnvironmentHost=true",
        "Entrypoint=/usr/local/bin/docker-entrypoint.sh",
        "Exec=postgres",
        "User=postgres:postgres",
        "Group=postgres",
        "GroupAdd=wheel",
        "WorkingDir=/var/lib/postgresql",
        "Volume=/tmp/pgdata:/var/lib/postgresql/data:z",
        "Mount=type=tmpfs,destination=/run/postgres",
        "Tmpfs=/run/postgres-tmp:rw,size=64m",
        "ReadOnly=true",
        "ReadOnlyTmpfs=true",
        "AddDevice=/dev/null:/dev/null:rwm",
        "AddCapability=NET_ADMIN",
        "DropCapability=AUDIT_WRITE",
        "ExposeHostPort=5432",
        "Memory=512m",
        "PidsLimit=2048",
        "Ulimit=nofile=1000:1000",
        "CgroupsMode=enabled",
        "LogDriver=journald",
        "LogOpt=tag=postgres",
        "Pull=missing",
        "RunInit=true",
        "StopSignal=SIGTERM",
        "StopTimeout=30",
        "TimeZone=UTC",
        "HealthCmd=",
        "pg_isready",
        "HealthInterval=30s",
        "HealthRetries=3",
        "HealthTimeout=5s",
        "HealthStartPeriod=10s",
        "HealthStartupCmd=",
        "pg_isready -t 1",
        "HealthStartupInterval=5s",
        "HealthStartupRetries=10",
        "HealthStartupSuccess=1",
        "HealthStartupTimeout=2s",
        "HealthLogDestination=local",
        "HealthMaxLogCount=5",
        "HealthMaxLogSize=500",
        "HealthOnFailure=restart",
        "Notify=healthy",
        "AutoUpdate=registry",
        "Network=test-net:ip=172.42.0.2",
        "AddHost=db.local:127.0.0.1",
        "PublishPort=5432:5432",
        "UIDMap=999:@1000",
        "GIDMap=999:@1000",
        "PodmanArgs=--no-hosts",
        "SecurityLabelType=container_t",
        "SecurityLabelLevel=s0:c1,c2",
        "SecurityLabelFileType=container_file_t",
        "SeccompProfile=/etc/containers/seccomp.json",
        "Mask=/proc/kcore",
        "Unmask=/sys/fs/cgroup",
        "NoNewPrivileges=true",
        "Sysctl=net.ipv4.ip_unprivileged_port_start=0",
        "HttpProxy=true",
        "Retry=3",
        "RetryDelay=2s",
        "PodmanArgs=",
        "--cidfile=/tmp/cid",
        "--rm",
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
