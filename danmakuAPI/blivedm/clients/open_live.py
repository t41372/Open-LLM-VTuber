# -*- coding: utf-8 -*-
import asyncio
import datetime
import hashlib
import hmac
import json
import logging
import uuid
from typing import *

import aiohttp

from . import ws_base

__all__ = (
    'OpenLiveClient',
)

logger = logging.getLogger('blivedm')

START_URL = 'https://live-open.biliapi.com/v2/app/start'
HEARTBEAT_URL = 'https://live-open.biliapi.com/v2/app/heartbeat'
END_URL = 'https://live-open.biliapi.com/v2/app/end'


class OpenLiveClient(ws_base.WebSocketClientBase):
    """
    开放平台客户端

    文档参考：https://open-live.bilibili.com/document/

    :param access_key_id: 在开放平台申请的access_key_id
    :param access_key_secret: 在开放平台申请的access_key_secret
    :param app_id: 在开放平台创建的项目ID
    :param room_owner_auth_code: 主播身份码
    :param session: cookie、连接池
    :param heartbeat_interval: 发送连接心跳包的间隔时间（秒）
    :param game_heartbeat_interval: 发送项目心跳包的间隔时间（秒）
    """

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        app_id: int,
        room_owner_auth_code: str,
        *,
        session: Optional[aiohttp.ClientSession] = None,
        heartbeat_interval=30,
        game_heartbeat_interval=20,
    ):
        super().__init__(session, heartbeat_interval)

        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        self._app_id = app_id
        self._room_owner_auth_code = room_owner_auth_code
        self._game_heartbeat_interval = game_heartbeat_interval

        # 在调用init_room后初始化的字段
        self._room_owner_uid: Optional[int] = None
        """主播用户ID"""
        self._room_owner_open_id: Optional[str] = None
        """主播Open ID"""
        self._host_server_url_list: Optional[List[str]] = []
        """弹幕服务器URL列表"""
        self._auth_body: Optional[str] = None
        """连接弹幕服务器用的认证包内容"""
        self._game_id: Optional[str] = None
        """项目场次ID"""

        # 在运行时初始化的字段
        self._game_heartbeat_timer_handle: Optional[asyncio.TimerHandle] = None
        """发项目心跳包定时器的handle"""

    @property
    def room_owner_uid(self) -> Optional[int]:
        """
        主播用户ID，调用init_room后初始化
        """
        return self._room_owner_uid

    @property
    def room_owner_open_id(self) -> Optional[str]:
        """
        主播Open ID，调用init_room后初始化
        """
        return self._room_owner_open_id

    @property
    def room_owner_auth_code(self):
        """
        主播身份码
        """
        return self._room_owner_auth_code

    @property
    def app_id(self):
        """
        在开放平台创建的项目ID
        """
        return self._app_id

    @property
    def game_id(self) -> Optional[str]:
        """
        项目场次ID，调用init_room后初始化
        """
        return self._game_id

    async def close(self):
        """
        释放本客户端的资源，调用后本客户端将不可用
        """
        if self.is_running:
            logger.warning('room=%s is calling close(), but client is running', self.room_id)

        if self._game_heartbeat_timer_handle is not None:
            self._game_heartbeat_timer_handle.cancel()
            self._game_heartbeat_timer_handle = None
        await self._end_game()

        await super().close()

    def _request_open_live(self, url, body: dict):
        body_bytes = json.dumps(body).encode('utf-8')
        headers = {
            'x-bili-accesskeyid': self._access_key_id,
            'x-bili-content-md5': hashlib.md5(body_bytes).hexdigest(),
            'x-bili-signature-method': 'HMAC-SHA256',
            'x-bili-signature-nonce': uuid.uuid4().hex,
            'x-bili-signature-version': '1.0',
            'x-bili-timestamp': str(int(datetime.datetime.now().timestamp())),
        }

        str_to_sign = '\n'.join(
            f'{key}:{value}'
            for key, value in headers.items()
        )
        signature = hmac.new(
            self._access_key_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256
        ).hexdigest()
        headers['Authorization'] = signature

        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        return self._session.post(url, headers=headers, data=body_bytes)

    async def init_room(self):
        """
        开启项目，并初始化连接房间需要的字段

        :return: 是否成功
        """
        if not await self._start_game():
            return False

        if self._game_id != '' and self._game_heartbeat_timer_handle is None:
            self._game_heartbeat_timer_handle = asyncio.get_running_loop().call_later(
                self._game_heartbeat_interval, self._on_send_game_heartbeat
            )
        return True

    async def _start_game(self):
        try:
            async with self._request_open_live(
                START_URL,
                {'code': self._room_owner_auth_code, 'app_id': self._app_id}
            ) as res:
                if res.status != 200:
                    logger.warning('_start_game() failed, status=%d, reason=%s', res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('_start_game() failed, code=%d, message=%s, request_id=%s',
                                   data['code'], data['message'], data['request_id'])
                    return False
                if not self._parse_start_game(data['data']):
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('_start_game() failed:')
            return False
        return True

    def _parse_start_game(self, data):
        self._game_id = data['game_info']['game_id']
        websocket_info = data['websocket_info']
        self._auth_body = websocket_info['auth_body']
        self._host_server_url_list = websocket_info['wss_link']
        anchor_info = data['anchor_info']
        self._room_id = anchor_info['room_id']
        self._room_owner_uid = anchor_info['uid']
        self._room_owner_open_id = anchor_info['open_id']
        return True

    async def _end_game(self):
        """
        关闭项目。建议关闭客户端时保证调用到这个函数（close会调用），否则可能短时间内无法重复连接同一个房间
        """
        if self._game_id in (None, ''):
            return True

        try:
            async with self._request_open_live(
                END_URL,
                {'app_id': self._app_id, 'game_id': self._game_id}
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _end_game() failed, status=%d, reason=%s',
                                   self._room_id, res.status, res.reason)
                    return False
                data = await res.json()
                code = data['code']
                if code != 0:
                    if code in (7000, 7003):
                        # 项目已经关闭了也算成功
                        return True

                    logger.warning('room=%d _end_game() failed, code=%d, message=%s, request_id=%s',
                                   self._room_id, code, data['message'], data['request_id'])
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _end_game() failed:', self._room_id)
            return False
        return True

    def _on_send_game_heartbeat(self):
        """
        定时发送项目心跳包的回调
        """
        self._game_heartbeat_timer_handle = asyncio.get_running_loop().call_later(
            self._game_heartbeat_interval, self._on_send_game_heartbeat
        )
        asyncio.create_task(self._send_game_heartbeat())

    async def _send_game_heartbeat(self):
        """
        发送项目心跳包
        """
        if self._game_id in (None, ''):
            logger.warning('game=%d _send_game_heartbeat() failed, game_id not found', self._game_id)
            return False

        try:
            # 保存一下，防止await之后game_id改变
            game_id = self._game_id
            async with self._request_open_live(
                HEARTBEAT_URL,
                {'game_id': game_id}
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _send_game_heartbeat() failed, status=%d, reason=%s',
                                   self._room_id, res.status, res.reason)
                    return False
                data = await res.json()
                code = data['code']
                if code != 0:
                    logger.warning('room=%d _send_game_heartbeat() failed, code=%d, message=%s, request_id=%s',
                                   self._room_id, code, data['message'], data['request_id'])

                    if code == 7003 and self._game_id == game_id:
                        # 项目异常关闭，可能是心跳超时，需要重新开启项目
                        self._need_init_room = True
                        if self._websocket is not None and not self._websocket.closed:
                            await self._websocket.close()

                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _send_game_heartbeat() failed:', self._room_id)
            return False
        return True

    async def _on_before_ws_connect(self, retry_count):
        """
        在每次建立连接之前调用，可以用来初始化房间
        """
        # 重连次数太多则重新init_room，保险
        reinit_period = max(3, len(self._host_server_url_list or ()))
        if retry_count > 0 and retry_count % reinit_period == 0:
            self._need_init_room = True
        await super()._on_before_ws_connect(retry_count)

    def _get_ws_url(self, retry_count) -> str:
        """
        返回WebSocket连接的URL，可以在这里做故障转移和负载均衡
        """
        return self._host_server_url_list[retry_count % len(self._host_server_url_list)]

    async def _send_auth(self):
        """
        发送认证包
        """
        await self._websocket.send_bytes(self._make_packet(self._auth_body, ws_base.Operation.AUTH))
