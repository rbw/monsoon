# -*- coding: utf-8 -*-

import asyncio

from aioli.utils.http import jsonify
from aioli.package.controller import BaseHttpController, BaseWebSocketController, route, input_load

from aioli_redis import RedisService

from .service import MonsoonService
from .schema import HostPath


class HttpController(BaseHttpController):
    def __init__(self):
        self.service = MonsoonService()

    @route('/test', 'GET')
    async def test(self, _):
        return jsonify(await self.service.relay_livestatus('hosts'))

    @route('/hosts', 'GET')
    async def hosts_get(self, _):
        return jsonify(await self.service.get_hosts())

    @route('/hosts/{host_name}', 'GET')
    @input_load(path=HostPath)
    async def host_get(self, host_name):
        return jsonify(await self.service.get_host(host_name))

    @route('/services', 'GET')
    async def services_get(self, _):
        return jsonify(await self.service.get_services())


class WebSocketController(BaseWebSocketController):
    path = '/hosts'
    redis = None

    def __init__(self, *args, **kwargs):
        self.service = MonsoonService()
        self.redis_service = RedisService()
        super(WebSocketController, self).__init__(*args, **kwargs)

    async def _create_listener(self, ws, sub):
        while True:
            msg = await sub.next_published()
            await ws.send_text(msg.value)

    async def on_connect(self, ws):
        self.redis, subscription = await self.redis_service.subscribe('hosts')
        asyncio.ensure_future(self._create_listener(ws, subscription))

        await ws.accept()

    async def on_disconnect(self, websocket, close_code):
        self.redis.close()
