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


def test_model(
    project: Project,
    state: str = "stopped",
    on_calendar: str | None = None,
    quadlet: bool = False,
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
            labels={{"app": "orchestrator"}},
            no_hosts=false,
            userns="keep-id",
            sub_uid_map="containers",
            sub_gid_map="containers",
            podman_args=["--infra"],
            global_args=["--log-level=info"],
            containers_conf_module=["/etc/containers/containers.conf"],
            dns=["1.1.1.1"],
            dns_search=["example.com"],
            dns_option=["ndots:1"],
            network_alias=["orchestrator"],
            ip="172.42.0.3",
            ip6="fd00::3",
            shm_size="256m",
            exit_policy="stop",
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
            hosts=[
                Host(host="orchestrator.local", ip="127.0.0.1"),
            ],
            uidmap=[
                IdMap(container_id="993", host_id="@1000"),
            ],
            gidmap=[
                IdMap(container_id="993", host_id="@1000"),
            ],
            volumes=[
                Volume(
                    source="/tmp/pod-data",
                    container_dir="/data",
                    options=["z"],
                ),
            ],
            extra_args=[
                ExtraArg(name="infra-name", value="orchestrator-infra", cmd="podman-pod-create"),
            ],
            containers=[
                podman::Container(
                    host=host,
                    name=f"{{pod.name}}-server",
                    image="ghcr.io/inmanta/orchestrator:latest",
                    user="993:993",
                    entrypoint="/usr/bin/inmanta",
                    command="-vvv --timed-logs server",
                    start_with_pod=true,
                ),
            ],
        )

        podman::services::SystemdPod(
            pod=pod,
            state={repr(state)},
            on_calendar={repr(on_calendar) if on_calendar is not None else "null"},
            enabled=true,
            systemd_unit_dir="/tmp/systemd/user",
            systemd_container_dir={'"/tmp/containers/systemd"' if quadlet else "null"},
            systemctl_command=["systemctl", "--user"],
            quadlet={"true" if quadlet else "false"},
        )
    """

    project.compile(model, no_dedent=False)


def test_all_options_in_command(project: Project) -> None:
    """
    Compile the model and verify that each Pod option is rendered into the
    generated systemd unit file (via the podman::pod_create cli command).
    """
    test_model(project, state="stopped")

    pod_unit_file_path = (
        pathlib.Path("/tmp/systemd/user") / "pod-inmanta-orchestrator.service"
    )
    unit_file_resource = next(
        r
        for r in project.resources.values()
        if getattr(r, "path", None) == str(pod_unit_file_path)
    )
    content = unit_file_resource.content

    expected = [
        "--module=/etc/containers/containers.conf",
        "--log-level=info",
        "pod create",
        "--exit-policy=stop",
        "--network=test-net:ip=172.42.0.3",
        "--network-alias=orchestrator",
        "--publish=127.0.0.1:8888:8888",
        "--add-host=orchestrator.local:127.0.0.1",
        "--hostname=inmanta-orchestrator",
        "--ip=172.42.0.3",
        "--ip6=fd00::3",
        "--dns=1.1.1.1",
        "--dns-search=example.com",
        "--dns-option=ndots:1",
        "--shm-size=256m",
        "--label=app=orchestrator",
        "--uidmap=993:@1000",
        "--gidmap=993:@1000",
        "--subuidname=containers",
        "--subgidname=containers",
        "--userns=keep-id",
        "--volume=/tmp/pod-data:/data:z",
        "--infra-name=orchestrator-infra",
        "--infra",
        "--name=inmanta-orchestrator",
    ]
    missing = [token for token in expected if token not in content]
    assert not missing, f"missing tokens in unit file: {missing}\ncontent:\n{content}"


def test_all_options_in_quadlet(project: Project) -> None:
    """
    Compile the model with quadlet enabled and verify each Pod option is
    rendered into the generated quadlet unit file.
    """
    test_model(project, state="stopped", quadlet=True)

    pod_unit_file_path = (
        pathlib.Path("/tmp/containers/systemd") / "pod-inmanta-orchestrator.pod"
    )
    unit_file_resource = next(
        r
        for r in project.resources.values()
        if getattr(r, "path", None) == str(pod_unit_file_path)
    )
    content = unit_file_resource.content

    expected = [
        "[Pod]",
        "PodName=inmanta-orchestrator",
        "HostName=inmanta-orchestrator",
        "Label=app=orchestrator",
        "UserNS=keep-id",
        "SubUIDMap=containers",
        "SubGIDMap=containers",
        "ContainersConfModule=/etc/containers/containers.conf",
        "GlobalArgs=",
        "--log-level=info",
        "DNS=1.1.1.1",
        "DNSSearch=example.com",
        "DNSOption=ndots:1",
        "IP=172.42.0.3",
        "IP6=fd00::3",
        "ShmSize=256m",
        "ExitPolicy=stop",
        "Volume=/tmp/pod-data:/data:z",
        "Network=test-net:ip=172.42.0.3",
        "NetworkAlias=orchestrator",
        "AddHost=orchestrator.local:127.0.0.1",
        "PublishPort=127.0.0.1:8888:8888",
        "UIDMap=993:@1000",
        "GIDMap=993:@1000",
        "PodmanArgs=",
        "--infra-name=orchestrator-infra",
        "--infra",
    ]
    missing = [token for token in expected if token not in content]
    assert not missing, f"missing tokens in unit file: {missing}\ncontent:\n{content}"


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


def test_deploy_quadlet(project: Project) -> None:
    # Make sure the pod can be deployed as a quadlet unit
    for state in ["configured", "stopped", "removed"]:
        # Compile the model
        test_model(project, state=state, quadlet=True)

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
