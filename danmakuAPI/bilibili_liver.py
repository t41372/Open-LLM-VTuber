# -*- coding: utf-8 -*-
import asyncio
import http.cookies
import random
from typing import *
import heapq
import time
import signal
import json
import yaml
import os

import aiohttp
import blivedm
import blivedm.models.web as web_models
import prompt_template

# 全局变量声明
session: Optional[aiohttp.ClientSession] = None
priority_queue = []
stop_event = asyncio.Event()
replied_messages = set()

# 优先级系统
PRIORITY_HIGH = 1  # 用于醒目留言和礼物
PRIORITY_NORMAL = 0  # 用于普通弹幕

class Config:
    """配置管理类"""
    def __init__(self):
        self.config = self._load_config()

        # B站配置
        self.room_id = int(self.config['BILIBILI']['ROOM_ID'])
        self.sessdata = self.config['BILIBILI'].get('SESSDATA', '')  # 使用get方法，没有时返回空字符串
        self.message_expire_time = self.config['BILIBILI'].get('MESSAGE_EXPIRE_TIME', 30)
        self.retry_interval = self.config['BILIBILI'].get('RETRY_INTERVAL', 3)

        # API配置
        self.api_port = self.config.get('PORT', 8000)
        self.api_host = self.config.get('HOST', '127.0.0.1')

    def _load_config(self) -> dict:
        """加载配置文件"""
        config_path = "conf.yaml"
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 验证必要的配置项
            if 'BILIBILI' not in config:
                raise ValueError("Missing BILIBILI configuration section")
            if 'ROOM_ID' not in config['BILIBILI']:
                raise ValueError("Missing BILIBILI.ROOM_ID configuration")

            return config
        except Exception as e:
            raise Exception(f"Error loading configuration: {str(e)}")

class MessageItem:
    def __init__(self, priority: int, text: str, timestamp: float):
        self.priority = priority
        self.text = text
        self.timestamp = timestamp

    def __lt__(self, other):
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.timestamp < other.timestamp

def init_session(config: Config):
    """初始化会话"""
    global session
    session = aiohttp.ClientSession()

    if config.sessdata:  # 只在有SESSDATA时设置cookie
        cookies = http.cookies.SimpleCookie()
        cookies['SESSDATA'] = config.sessdata
        cookies['SESSDATA']['domain'] = 'bilibili.com'
        session.cookie_jar.update_cookies(cookies)

async def send_to_ai_vtuber(config: Config, text: str, priority: int):
    """发送消息到AI VTuber"""
    url = f"http://{config.api_host}:{config.api_port}/textinput"
    headers = {"Content-Type": "application/json"}
    data = {
        "text": text,
        "priority": priority
    }

    async with aiohttp.ClientSession() as session:
        while not stop_event.is_set():
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    response_data = await response.json()
                    error_code = response_data.get("error_code", 0)

                    if error_code == 0:
                        # 成功发送
                        print(f"Successfully sent to AI VTuber: {text} (priority: {priority})")
                        break
                    elif error_code == 4001:
                        # 系统繁忙，需要重试
                        print(f"System busy. Retrying in {config.retry_interval} seconds...")
                        await asyncio.sleep(config.retry_interval)
                    else:
                        # 其他错误
                        print(f"Failed to send to AI VTuber: {response_data}")
                        break
            except Exception as e:
                print(f"Error sending message: {e}")
                break

async def process_queue(config: Config):
    """处理消息队列"""
    while not stop_event.is_set():
        if priority_queue:
            current_time = time.time()
            message = heapq.heappop(priority_queue)

            # 检查消息是否过期
            if current_time - message.timestamp > config.message_expire_time:
                continue

            await send_to_ai_vtuber(config, message.text, message.priority)

            if message.priority == PRIORITY_NORMAL:
                replied_messages.add(message.text)

            await asyncio.sleep(1)
        else:
            await asyncio.sleep(0.5)

class MyHandler(blivedm.BaseHandler):
    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        print(f'[{client.room_id}] {message.uname}：{message.msg}')
        if message.msg not in replied_messages:
            prompt = prompt_template.danmaku_prompt('danmaku', message.uname, message.msg)
            heapq.heappush(priority_queue, 
                          MessageItem(PRIORITY_NORMAL, prompt, time.time()))

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        print(f'[{client.room_id}] {message.uname} 赠送{message.gift_name}x{message.num}'
              f' （{message.coin_type}瓜子x{message.total_coin}）')
        prompt = prompt_template.danmaku_prompt('gift', message.uname, 
                                              f"{message.gift_name}x{message.num}")
        heapq.heappush(priority_queue, 
                      MessageItem(PRIORITY_HIGH, prompt, time.time()))

    def _on_buy_guard(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        print(f'[{client.room_id}] {message.username} 购买{message.gift_name}')
        prompt = prompt_template.danmaku_prompt('gift', message.username, message.gift_name)
        heapq.heappush(priority_queue, 
                      MessageItem(PRIORITY_HIGH, prompt, time.time()))

    def _on_super_chat(self, client: blivedm.BLiveClient, message: web_models.SuperChatMessage):
        print(f'[{client.room_id}] 醒目留言 ¥{message.price} {message.uname}：{message.message}')
        prompt = prompt_template.danmaku_prompt('super_chat', message.uname, message.message)
        heapq.heappush(priority_queue, 
                      MessageItem(PRIORITY_HIGH, prompt, time.time()))

async def run_single_client(config: Config):
    """运行单个直播间监听客户端"""
    client = blivedm.BLiveClient(config.room_id, session=session)
    handler = MyHandler()
    client.set_handler(handler)

    client.start()
    try:
        asyncio.create_task(process_queue(config))
        await stop_event.wait()
    finally:
        await client.stop_and_close()

async def main():
    """主函数"""
    try:
        config = Config()
        init_session(config)
        print("开始监听...")
        try:
            await run_single_client(config)
        finally:
            await session.close()
    except Exception as e:
        print(f"Error in main: {e}")
        stop_event.set()

def signal_handler(sig, frame):
    """信号处理函数"""
    print("Received termination signal. Stopping...")
    stop_event.set()

if __name__ == '__main__':
    try:
        # 注册信号处理函数
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        asyncio.run(main())
    except Exception as e:
        print(f"Error running bilibili danmaku client: {e}")