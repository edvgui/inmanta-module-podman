# `podman::Container` configuration reference

Mapping between attributes of the `podman::Container` entity (and the
`podman::ContainerLike` base entity), the corresponding `podman container run`
CLI option, and the corresponding `[Container]` key in a quadlet
`*.container` unit file.

References:
- https://docs.podman.io/en/latest/markdown/podman-container-run.1.html
- https://docs.podman.io/en/latest/markdown/podman-container.unit.5.html

## Inherited from `podman::ContainerLike`

| Entity attribute          | Podman CLI option        | Quadlet `[Container]` key |
| ------------------------- | ------------------------ | ------------------------- |
| `name`                    | `--name`                 | `ContainerName`           |
| `hostname`                | `--hostname`             | `HostName`                |
| `labels`                  | `--label`                | `Label`                   |
| `no_hosts`                | `--no-hosts`             | `PodmanArgs=--no-hosts`   |
| `userns`                  | `--userns`               | `UserNS`                  |
| `sub_uid_map`             | `--subuidname`           | `SubUIDMap`               |
| `sub_gid_map`             | `--subgidname`           | `SubGIDMap`               |
| `podman_args`             | (passthrough, at end)    | `PodmanArgs`              |
| `global_args`             | (passthrough, after cmd) | `GlobalArgs`              |
| `containers_conf_module`  | `--module`               | `ContainersConfModule`    |
| `dns`                     | `--dns`                  | `DNS`                     |
| `dns_search`              | `--dns-search`           | `DNSSearch`               |
| `dns_option`              | `--dns-option`           | `DNSOption`               |
| `network_alias`           | `--network-alias`        | `NetworkAlias`            |
| `ip`                      | `--ip`                   | `IP`                      |
| `ip6`                     | `--ip6`                  | `IP6`                     |
| `shm_size`                | `--shm-size`             | `ShmSize`                 |
| `networks`                | `--network`              | `Network`                 |
| `hosts`                   | `--add-host`             | `AddHost`                 |
| `publish`                 | `--publish`              | `PublishPort`             |
| `uidmap`                  | `--uidmap`               | `UIDMap`                  |
| `gidmap`                  | `--gidmap`               | `GIDMap`                  |
| `volumes`                 | `--volume`               | `Volume`                  |
| `extra_args`              | `--<name>=<value>`       | `PodmanArgs`              |

## `podman::Container`-specific attributes

| Entity attribute     | Podman CLI option                       | Quadlet `[Container]` key |
| -------------------- | --------------------------------------- | ------------------------- |
| `image`              | (positional, after options)             | `Image`                   |
| `command`            | (positional, after image)               | `Exec`                    |
| `entrypoint`         | `--entrypoint`                          | `Entrypoint`              |
| `env`                | `--env`                                 | `Environment`             |
| `env_file`           | `--env-file`                            | `EnvironmentFile`         |
| `environment_host`   | `--env-host`                            | `EnvironmentHost`         |
| `user`               | `--user`                                | `User`                    |
| `group`              | `--group`                               | `Group`                   |
| `group_add`          | `--group-add`                           | `GroupAdd`                |
| `working_dir`        | `--workdir`                             | `WorkingDir`              |
| `annotations`        | `--annotation`                          | `Annotation`              |
| `expose_host_port`   | `--expose`                              | `ExposeHostPort`          |
| `mount`              | `--mount`                               | `Mount`                   |
| `tmpfs`              | `--tmpfs`                               | `Tmpfs`                   |
| `read_only`          | `--read-only`                           | `ReadOnly`                |
| `read_only_tmpfs`    | `--read-only-tmpfs`                     | `ReadOnlyTmpfs`           |
| `add_device`         | `--device`                              | `AddDevice`               |
| `add_capability`     | `--cap-add`                             | `AddCapability`           |
| `drop_capability`    | `--cap-drop`                            | `DropCapability`          |
| `memory`             | `--memory`                              | `Memory`                  |
| `pids_limit`         | `--pids-limit`                          | `PidsLimit`               |
| `ulimit`             | `--ulimit`                              | `Ulimit`                  |
| `cgroups_mode`       | `--cgroups`                             | `CgroupsMode`             |
| `log_driver`         | `--log-driver`                          | `LogDriver`               |
| `log_opt`            | `--log-opt`                             | `LogOpt`                  |
| `pull`               | `--pull`                                | `Pull`                    |
| `run_init`           | `--init`                                | `RunInit`                 |
| `stop_signal`        | `--stop-signal`                         | `StopSignal`              |
| `stop_timeout`       | `--stop-timeout`                        | `StopTimeout`             |
| `timezone`           | `--tz`                                  | `TimeZone`                |
| `notify`             | `--sdnotify`                            | `Notify`                  |
| `auto_update`        | `--label=io.containers.autoupdate=<v>`  | `AutoUpdate`              |
| `pod`                | `--pod` (or `--pod-id-file` via systemd)| `Pod`                     |
| `start_with_pod`     | (quadlet-only)                          | `StartWithPod`            |
| `seccomp_profile`    | `--security-opt=seccomp=<value>`        | `SeccompProfile`          |
| `mask`               | `--security-opt=mask=<value>`           | `Mask`                    |
| `unmask`             | `--security-opt=unmask=<value>`         | `Unmask`                  |
| `no_new_privileges`  | `--security-opt=no-new-privileges`      | `NoNewPrivileges`         |
| `sysctl`             | `--sysctl`                              | `Sysctl`                  |
| `rootfs`             | `--rootfs`                              | `Rootfs`                  |
| `http_proxy`         | `--http-proxy`                          | `HttpProxy`               |
| `retry`              | `--retry`                               | `Retry`                   |
| `retry_delay`        | `--retry-delay`                         | `RetryDelay`              |

## `podman::container::Health` attributes (via `Container.health`)

| Entity attribute    | Podman CLI option           | Quadlet `[Container]` key |
| ------------------- | --------------------------- | ------------------------- |
| `cmd`               | `--health-cmd`              | `HealthCmd`               |
| `interval`          | `--health-interval`         | `HealthInterval`          |
| `retries`           | `--health-retries`          | `HealthRetries`           |
| `timeout`           | `--health-timeout`          | `HealthTimeout`           |
| `start_period`      | `--health-start-period`     | `HealthStartPeriod`       |
| `startup_cmd`       | `--health-startup-cmd`      | `HealthStartupCmd`        |
| `startup_interval`  | `--health-startup-interval` | `HealthStartupInterval`   |
| `startup_retries`   | `--health-startup-retries`  | `HealthStartupRetries`    |
| `startup_success`   | `--health-startup-success`  | `HealthStartupSuccess`    |
| `startup_timeout`   | `--health-startup-timeout`  | `HealthStartupTimeout`    |
| `log_destination`   | `--health-log-destination`  | `HealthLogDestination`    |
| `max_log_count`     | `--health-max-log-count`    | `HealthMaxLogCount`       |
| `max_log_size`      | `--health-max-log-size`     | `HealthMaxLogSize`        |
| `on_failure`        | `--health-on-failure`       | `HealthOnFailure`         |

## `podman::container::SecurityLabel` attributes (via `Container.security_label`)

| Entity attribute | Podman CLI option                    | Quadlet `[Container]` key |
| ---------------- | ------------------------------------ | ------------------------- |
| `disable`        | `--security-opt=label=disable`       | `SecurityLabelDisable`    |
| `type`           | `--security-opt=label=type:<value>`  | `SecurityLabelType`       |
| `level`          | `--security-opt=label=level:<value>` | `SecurityLabelLevel`      |
| `file_type`      | `--security-opt=label=filetype:<v>`  | `SecurityLabelFileType`   |
| `nested`         | `--security-opt=label=nested`        | `SecurityLabelNested`     |
