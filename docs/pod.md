# `podman::Pod` configuration reference

Mapping between attributes of the `podman::Pod` entity (and the
`podman::ContainerLike` base entity), the corresponding `podman pod create`
CLI option, and the corresponding `[Pod]` key in a quadlet `*.pod` unit file.

References:
- https://docs.podman.io/en/latest/markdown/podman-pod-create.1.html
- https://docs.podman.io/en/latest/markdown/podman-pod.unit.5.html

## Inherited from `podman::ContainerLike`

| Entity attribute          | Podman CLI option        | Quadlet `[Pod]` key     |
| ------------------------- | ------------------------ | ----------------------- |
| `name`                    | `--name`                 | `PodName`               |
| `hostname`                | `--hostname`             | `HostName`              |
| `labels`                  | `--label`                | `Label`                 |
| `no_hosts`                | `--no-hosts`             | `PodmanArgs=--no-hosts` |
| `userns`                  | `--userns`               | `UserNS`                |
| `sub_uid_map`             | `--subuidname`           | `SubUIDMap`             |
| `sub_gid_map`             | `--subgidname`           | `SubGIDMap`             |
| `podman_args`             | (passthrough, at end)    | `PodmanArgs`            |
| `global_args`             | (passthrough, after cmd) | `GlobalArgs`            |
| `containers_conf_module`  | `--module`               | `ContainersConfModule`  |
| `dns`                     | `--dns`                  | `DNS`                   |
| `dns_search`              | `--dns-search`           | `DNSSearch`             |
| `dns_option`              | `--dns-option`           | `DNSOption`             |
| `network_alias`           | `--network-alias`        | `NetworkAlias`          |
| `ip`                      | `--ip`                   | `IP`                    |
| `ip6`                     | `--ip6`                  | `IP6`                   |
| `shm_size`                | `--shm-size`             | `ShmSize`               |
| `networks`                | `--network`              | `Network`               |
| `hosts`                   | `--add-host`             | `AddHost`               |
| `publish`                 | `--publish`              | `PublishPort`           |
| `uidmap`                  | `--uidmap`               | `UIDMap`                |
| `gidmap`                  | `--gidmap`               | `GIDMap`                |
| `volumes`                 | `--volume`               | `Volume`                |
| `extra_args`              | `--<name>=<value>`       | `PodmanArgs`            |

## `podman::Pod`-specific attributes

| Entity attribute | Podman CLI option | Quadlet `[Pod]` key |
| ---------------- | ----------------- | ------------------- |
| `exit_policy`    | `--exit-policy`   | `ExitPolicy`        |
