# Changelog

## v1.14.1 - ?

- Add `podman::services::SystemdContainer.success_exit_status` (`SuccessExitStatus=`), `["143"]` by default: a container that doesn't handle the stop signal exits with 143 when it is stopped, which marked its unit as failed and triggered its `on_failure` units on every restart (deploy, auto-update).  Requires files >= 2.12.1
- A `podman::services::SystemdService` of a template unit (`name@.service`) only manages its files, it doesn't get a `files::SystemdUnit` anymore: systemctl can't query a template, only its instances, so the resource always failed (e.g. a template only started by `OnFailure=`, `state="configured"` and `enabled=false`).  `SystemdService.systemd_unit` is now optional

## v1.14.0 - 2026-11-11

- Manage the state of the units of `podman::services::SystemdService` with `files::SystemdUnit` instead of `exec::Run` commands: a unit that fails to start reports its journal, and pending changes show in dry-runs
- The `restart` state of `podman::services::SystemdService` now only restarts the unit when its files changed since it started, instead of on every deploy.  Other files can be added to `SystemdService.systemd_unit.config_files`
- The module doesn't depend on the `exec` module anymore
- The timer of a `podman::services::SystemdService` (`on_calendar`) doesn't `Requires=` its service anymore: starting the timer (at boot, or when a deploy starts or restarts it) ran the service right away, e.g. `podman-auto-update` updated the containers in the middle of the day
- `podman::services::SystemdAutoUpdate` waits for the network to be online: its unit had `After=network-online.service` (not a unit) instead of `network-online.target`, or `podman-user-wait-network-online.service` for a user manager

## v1.13.4 - 2026-10-25

- Add `podman::services::SystemdContainer.wanted_by`, other units that pull the container in (`WantedBy=`) on top of `default.target`, e.g. a mount it needs

## v1.13.3 - 2026-10-18

- Add `podman::services::UnmanagedSystemdUnit`, to make a `SystemdContainer` depend on a systemd unit this module doesn't manage: `dependencies` now accepts any `SystemdUnitABC`

## v1.13.2 - 2026-09-29

- Allow publishing the same container port once per protocol (e.g. tcp and udp)
- Wrap ipv6 addresses in brackets when publishing ports

## v1.13.1 - 2026-07-12

- Fix ImageFromRegistry dryrun by checking digest of registry image

## v1.13.0 - 2026-07-12

- Add a configurable `pull_timeout` to `podman::ImageFromRegistry` (defaults to null, i.e. no timeout)
- Add a configurable `build_timeout` to `podman::ImageFromSource` (defaults to null, i.e. no timeout)
- Apply a timeout to the internal `whoami` command so a hung connection can no longer stall a deployment indefinitely


## v1.12.0 - 2026-07-11

- Allow expressing dependencies between container services (`Requires=`/`After=`)


## v1.11.3 - 2026-06-28

- Fix diffing of bridge routes when destinations are repeated with different metrics.

## v1.11.2 - 2026-06-28 (YANKED)

- Fix route index, to include the metric, allowing multiple routes towards a given destination.

## v1.11.1 - 2026-06-20

- Allow using references in quadlet units

## v1.11.0 - 2026-05-25

- Support all container and pod quadlet unit configuration options
- Add quadlet mode for pod systemd services
- Don't require std::AgentConfig

## v1.10.1 - 2026-04-21

- Fix subnets/routes diffing for podman::Network

## v1.10.0 - 2026-04-05

- Allow to configure routes on a subnet

## v1.9.0 - 2025-10-25

- Improve input quoting in generated units
- Add freeform podman args to ContainerLike entity

## v1.8.1 - 2025-08-17

- Add missing wiring of on_failure option

## v1.8.0 - 2025-08-17

- Configure OnFailure directive for quadlet services
- Quote environment variables in quadlet file

## v1.7.0 - 2025-07-06

- Expose systemd service resources via relations

## v1.6.0 - 2025-06-14

- Add quadlet mode for container systemd services

## v1.5.1 - 2025-05-29

- Improve dry-runs of podman network resources

## v1.5.0 - 2025-05-29

- Allow to manage network options and labels

## v1.4.1 - 2025-04-20

- Make sure container and pod units wait on podman-user-wait-network-online.service when running rootless.

## v1.4.0 - 2025-04-11

- Fix socket unit file install target
- Use python type annotations in plugins

## v1.3.0 - 2025-01-03

- Add userns option support to container-like entities

## v1.2.0 - 2024-12-21

- Add support for configuring podman-auto-update service
- Fix usage of labels on container/pod resources

## v1.1.0 - 2024-12-13

- Add listen_stream to container service for socket activation support

## v1.0.1 - 2024-09-29

- Bump dependencies

## v1.0.0 - 2024-09-03

- Use mitogen for handler io

## v0.7.1 - 2024-07-07

- Re-release of 0.7.0

## v0.7.0 - 2024-07-07

- Fix service enabling, using full path as symlink target
- Allow to provide any arg, for any command used to manage pod/containers, on the ContainerLike entity

## v0.6.0 - 2024-05-28

- Specify systemd unit folder for SystemdContainer/Pod service

## v0.5.0 - 2024-05-25

- Support periodic, short-lived container-based services.

## v0.4.2 - 2024-05-16

- Always detect change when no image digest is specified

## v0.4.1 - 2024-05-09

- Make sure to login as the new user when becoming the resource owner user

## v0.4.0 - 2024-04-28

- Manage extra hosts in container's /etc/hosts file

## v0.3.1 - 2024-04-18

- Fix unmanaged resource usage

## v0.3.0 - 2024-04-07

- Disable timeout for image build/pull.
- Add `configured` state to pod/container service.
- Set `send_event=true` for systemd_service files.

## v0.2.0 - 2024-03-17

- More indexes of module resources to resource entities.
- Add podman::ImageDiscovery resource.
- Add podman::NetworkDiscovery resource.

## v0.1.0 - 2024-03-10

- Add support for podman Image
- Add support for podman Network
- Add support for systemd container and pod services
