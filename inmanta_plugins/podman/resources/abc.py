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
import fabric

import inmanta.agent.handler
import inmanta.execute.proxy
import inmanta.export
import inmanta.resources


class ResourceABC(inmanta.resources.PurgeableResource):
    fields = ("host",)

    @classmethod
    def get_host(
        cls,
        exporter: inmanta.export.Exporter,
        entity: inmanta.execute.proxy.DynamicProxy,
    ) -> dict:
        """
        Build the host config, containing the information required to reach the
        host.
        """
        return {
            "host": entity.host.host,
        }


class HandlerABC(inmanta.agent.handler.CRUDHandler):
    def pre(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: inmanta.resources.Resource,
    ) -> None:
        self.connection = fabric.Connection(**resource.host)
        return super().pre(ctx, resource)

    def post(
        self,
        ctx: inmanta.agent.handler.HandlerContext,
        resource: inmanta.resources.Resource,
    ) -> None:
        self.connection.close()
        return super().post(ctx, resource)
