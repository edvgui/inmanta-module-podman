"""
    Copyright 2023 Guillaume Everarts de Velp

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

import json
import typing

import inmanta.agent.handler
import inmanta.const
import inmanta.execute.proxy
import inmanta.export
import inmanta.resources
import inmanta_plugins.podman.resources.abc


def valid_digest(digest: str, repo_digests: list[str]) -> bool:
    """
    Check if the given digest value is a match for one of the repo digests
    entries.  The format of the repo digests is <repository>:<tag>@<digest>

    :param digest: The digest to validate
    :param repo_digests: The list of repo digest to compare it to
    """
    return digest in [repo_digest.split("@")[-1] for repo_digest in repo_digests]


class ImageResource(inmanta_plugins.podman.resources.abc.ResourceABC):
    fields = ("digest",)
    digest: str | None


IR = typing.TypeVar("IR", bound=ImageResource)


class ImageHandler(
    inmanta_plugins.podman.resources.abc.HandlerABC[IR],
    inmanta.agent.handler.CRUDHandlerGeneric[IR],
):
    def inspect_image(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: IR,
    ) -> dict:
        # Run the inspect command on the remote host
        command = ["podman", "image", "inspect", resource.name]
        stdout, stderr, ret = self.run_command(
            ctx,
            resource,
            command=command,
            timeout=5,
        )

        # If we receive an empty list, our network doesn't exist
        if stdout.strip() == "[]":
            ctx.info("%(stderr)s", stderr=stderr)
            raise LookupError()

        # If the command failed, something went wrong
        if ret != 0:
            ctx.error(
                "%(stderr)s",
                exit_code=ret,
                stderr=stderr,
            )
            raise RuntimeError("Failed to inspect image")

        return json.loads(stdout)[0]

    def calculate_diff(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        current: IR,
        desired: IR,
    ) -> dict[str, dict[str, typing.Any]]:
        changes = super().calculate_diff(ctx, current, desired)

        if not changes and desired.digest is None:
            # When there is no change and there is no desired digest, force the detection
            # of a change by including the digest in the diff
            changes["digest"] = {"current": current.digest, "desired": None}

        return changes

    def delete_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: IR,
    ) -> None:
        # Run the remove command on the remote host
        command = ["podman", "image", "rm", resource.name]
        _, stderr, ret = self.run_command(
            ctx,
            resource,
            command=command,
            timeout=5,
        )

        # If the command failed, something went wrong
        if ret != 0:
            ctx.error(
                "%(stderr)s",
                exit_code=ret,
                stderr=stderr,
            )
            raise RuntimeError("Failed to remove image")

        ctx.set_purged()


@inmanta.resources.resource(
    name="podman::ImageFromSource",
    id_attribute="q",
    agent="host.name",
)
class ImageFromSourceResource(ImageResource):
    fields = (
        "options",
        "context",
    )
    options: list[str]
    context: typing.Optional[str]

    @classmethod
    def get_options(
        cls,
        exporter: inmanta.export.Exporter,
        entity: inmanta.execute.proxy.DynamicProxy,
    ) -> list[str]:
        """
        Create the list of options that can be used to build the image.
        """
        options: list[str] = []
        if entity.squash:
            options.append("--squash")
        if entity.squash_all:
            options.append("--squash-all")
        if entity.pull:
            options.append(f"--pull={entity.pull}")
        if entity.file:
            options.append(f"--file={entity.file}")
        return options

    @classmethod
    def get_digest(
        cls,
        exporter: inmanta.export.Exporter,
        entity: inmanta.execute.proxy.DynamicProxy,
    ) -> None:
        """
        The digest can't be known before building the image, so we just
        return None
        """
        return None


@inmanta.agent.handler.provider("podman::ImageFromSource", "")
class ImageFromSourceHandler(ImageHandler[ImageFromSourceResource]):
    def read_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ImageFromSourceResource,
    ) -> None:
        try:
            existing_image = self.inspect_image(ctx, resource)
        except LookupError:
            # The image was not found
            raise inmanta.agent.handler.ResourcePurged()

        resource.digest = existing_image["Digest"]

    def build_image(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ImageFromSourceResource,
    ) -> None:
        # Create build command
        cmd = [
            "podman",
            "image",
            "build",
            f"--tag={resource.name}",
            *resource.options,
        ]
        if resource.context is not None:
            cmd.append(resource.context)

        # Run the create command on the remote host
        _, stderr, ret = self.run_command(
            ctx,
            resource,
            command=cmd,
            timeout=None,
        )

        # If the command failed, something went wrong
        if ret != 0:
            ctx.error(
                "%(stderr)s",
                exit_code=ret,
                stderr=stderr,
            )
            raise RuntimeError("Failed to build image")

    def create_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ImageFromSourceResource,
    ) -> None:
        self.build_image(ctx, resource)
        ctx.set_created()

    def update_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        changes: dict[str, dict[str, object]],
        resource: ImageFromSourceResource,
    ) -> None:
        self.build_image(ctx, resource)

        if not valid_digest(
            changes["digest"]["current"],
            self.inspect_image(ctx, resource)["RepoDigests"],
        ):
            # If the digest has changed, we have a different image
            ctx.set_updated()


@inmanta.resources.resource(
    name="podman::ImageFromRegistry",
    id_attribute="q",
    agent="host.name",
)
class ImageFromRegistryResource(ImageResource):
    fields = ("transport", "digest")
    transport: typing.Optional[str]
    digest: typing.Optional[str]


@inmanta.agent.handler.provider("podman::ImageFromRegistry", "")
class ImageFromRegistryHandler(ImageHandler[ImageFromRegistryResource]):
    def read_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ImageFromRegistryResource,
    ) -> None:
        try:
            existing_image = self.inspect_image(ctx, resource)
        except LookupError:
            # The image was not found
            raise inmanta.agent.handler.ResourcePurged()

        if not valid_digest(resource.digest, existing_image["RepoDigests"]):
            # Only detect a different digest if the desired digest (which may be None)
            # is not part of the image ones
            resource.digest = existing_image["Digest"]

    def pull_image(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ImageFromRegistryResource,
    ) -> None:
        # Compose image source
        source = resource.name
        if resource.transport is not None:
            source = f"{resource.transport}{source}"
        if resource.digest is not None:
            source = f"{source}@{resource.digest}"

        # Run the create command on the remote host
        _, stderr, ret = self.run_command(
            ctx,
            resource,
            command=["podman", "image", "pull", source],
            timeout=None,
        )

        # If the command failed, something went wrong
        if ret != 0:
            ctx.error(
                "%(stderr)s",
                exit_code=ret,
                stderr=stderr,
            )
            raise RuntimeError("Failed to pull image")

    def create_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: ImageFromRegistryResource,
    ) -> None:
        self.pull_image(ctx, resource)
        ctx.set_created()

    def update_resource(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        changes: dict[str, dict[str, object]],
        resource: ImageFromRegistryResource,
    ) -> None:
        self.pull_image(ctx, resource)

        if not valid_digest(
            changes["digest"]["current"],
            self.inspect_image(ctx, resource)["RepoDigests"],
        ):
            # If the digest has changed, we have a different image
            ctx.set_updated()
