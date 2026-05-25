# inmanta-module-podman

[![pypi version](https://img.shields.io/pypi/v/inmanta-module-podman.svg)](https://pypi.python.org/pypi/inmanta-module-podman/)
[![build status](https://img.shields.io/github/actions/workflow/status/edvgui/inmanta-module-podman/continuous-integration.yml)](https://github.com/edvgui/inmanta-module-podman/actions)

This package is an adapter that is meant to be used with the inmanta orchestrator: https://docs.inmanta.com

## Features

This module allows to manage [podman](https://podman.io) resources, on a unix host.  It contains the following resources:
1. `podman::Network`: to manage a podman network (subnets, routes, dns, driver, labels, options, ...).
2. `podman::NetworkDiscovery`: to discover existing podman networks owned by a user on a host.
3. `podman::Pod`: to manage a podman pod, including its networking, port publishing, id mapping and shared resources.
4. `podman::Container`: to manage a podman container (image, command, environment, volumes, networks, healthcheck, security label, resource limits, auto-update, ...).
5. `podman::Image`, `podman::ImageFromRegistry` and `podman::ImageFromSource`: to make sure a container image is present on a host, either pulled from a registry or built from a `Containerfile`.
6. `podman::ImageDiscovery`: to discover existing container images owned by a user on a host.
7. `podman::AutoUpdate`: to configure the podman auto-update service for a given user.
8. `podman::services::SystemdContainer`, `podman::services::SystemdPod` and `podman::services::SystemdAutoUpdate`: to wrap a container, a pod or the auto-update service into a systemd service.  These services can either be generated as plain systemd unit files (calling the `podman` cli) or as [quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html) unit files.

## Example

The following example shows how to run a container as a systemd service, using a quadlet unit file.  The container is a simple nginx web server, exposing its port 80 on the host port 8080.

<x-example-quadlet>

```
import mitogen
import podman
import podman::container_like
import podman::services
import std

host = std::Host(
    name="localhost",
    os=std::linux,
    via=mitogen::Local(),
)

# Make sure the container image is present on the host
image = podman::ImageFromRegistry(
    host=host,
    name="docker.io/library/nginx:latest",
)

# Define the container
web = podman::Container(
    host=host,
    name="nginx-web",
    image=image.name,
    publish=[
        podman::container_like::Publish(host_port="8080", container_port="80"),
    ],
)

# Wrap the container into a systemd service, using a quadlet unit file
podman::services::SystemdContainer(
    container=web,
    state="running",
    enabled=true,
    systemd_unit_dir="/etc/systemd/system",
    systemd_container_dir="/etc/containers/systemd",
    quadlet=true,
)

```

</x-example-quadlet>

Find more examples in the `tests` folder of this module!
