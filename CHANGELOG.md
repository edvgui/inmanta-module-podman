# Changelog

## v1.9.0 - ?

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
