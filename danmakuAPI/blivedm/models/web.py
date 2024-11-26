# -*- coding: utf-8 -*-
import dataclasses
import json
from typing import *

__all__ = (
    'HeartbeatMessage',
    'DanmakuMessage',
    'GiftMessage',
    'GuardBuyMessage',
    'SuperChatMessage',
    'SuperChatDeleteMessage',
)


@dataclasses.dataclass
class HeartbeatMessage:
    """
    心跳消息
    """

    popularity: int = 0
    """人气值，已废弃"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            popularity=data['popularity'],
        )


@dataclasses.dataclass
class DanmakuMessage:
    """
    弹幕消息
    """

    mode: int = 0
    """弹幕显示模式（滚动、顶部、底部）"""
    font_size: int = 0
    """字体尺寸"""
    color: int = 0
    """颜色"""
    timestamp: int = 0
    """时间戳（毫秒）"""
    rnd: int = 0
    """随机数，前端叫作弹幕ID，可能是去重用的"""
    uid_crc32: str = ''
    """用户ID文本的CRC32"""
    msg_type: int = 0
    """是否礼物弹幕（节奏风暴）"""
    bubble: int = 0
    """右侧评论栏气泡"""
    dm_type: int = 0
    """弹幕类型，0文本，1表情，2语音"""
    emoticon_options: Union[dict, str] = ''
    """表情参数"""
    voice_config: Union[dict, str] = ''
    """语音参数"""
    mode_info: dict = dataclasses.field(default_factory=dict)
    """一些附加参数"""

    msg: str = ''
    """弹幕内容"""

    uid: int = 0
    """用户ID"""
    uname: str = ''
    """用户名"""
    admin: int = 0
    """是否房管"""
    vip: int = 0
    """是否月费老爷"""
    svip: int = 0
    """是否年费老爷"""
    urank: int = 0
    """用户身份，用来判断是否正式会员，猜测非正式会员为5000，正式会员为10000"""
    mobile_verify: int = 0
    """是否绑定手机"""
    uname_color: str = ''
    """用户名颜色"""

    medal_level: str = ''
    """勋章等级"""
    medal_name: str = ''
    """勋章名"""
    runame: str = ''
    """勋章房间主播名"""
    medal_room_id: int = 0
    """勋章房间ID"""
    mcolor: int = 0
    """勋章颜色"""
    special_medal: str = ''
    """特殊勋章"""

    user_level: int = 0
    """用户等级"""
    ulevel_color: int = 0
    """用户等级颜色"""
    ulevel_rank: str = ''
    """用户等级排名，>50000时为'>50000'"""

    old_title: str = ''
    """旧头衔"""
    title: str = ''
    """头衔"""

    privilege_type: int = 0
    """舰队类型，0非舰队，1总督，2提督，3舰长"""

    @classmethod
    def from_command(cls, info: list):
        if len(info[3]) != 0:
            medal_level = info[3][0]
            medal_name = info[3][1]
            runame = info[3][2]
            room_id = info[3][3]
            mcolor = info[3][4]
            special_medal = info[3][5]
        else:
            medal_level = 0
            medal_name = ''
            runame = ''
            room_id = 0
            mcolor = 0
            special_medal = 0

        if len(info[5]) != 0:
            old_title = info[5][0]
            title = info[5][1]
        else:
            old_title = ''
            title = ''

        return cls(
            mode=info[0][1],
            font_size=info[0][2],
            color=info[0][3],
            timestamp=info[0][4],
            rnd=info[0][5],
            uid_crc32=info[0][7],
            msg_type=info[0][9],
            bubble=info[0][10],
            dm_type=info[0][12],
            emoticon_options=info[0][13],
            voice_config=info[0][14],
            mode_info=info[0][15],

            msg=info[1],

            uid=info[2][0],
            uname=info[2][1],
            admin=info[2][2],
            vip=info[2][3],
            svip=info[2][4],
            urank=info[2][5],
            mobile_verify=info[2][6],
            uname_color=info[2][7],

            medal_level=medal_level,
            medal_name=medal_name,
            runame=runame,
            medal_room_id=room_id,
            mcolor=mcolor,
            special_medal=special_medal,

            user_level=info[4][0],
            ulevel_color=info[4][2],
            ulevel_rank=info[4][3],

            old_title=old_title,
            title=title,

            privilege_type=info[7],
        )

    @property
    def emoticon_options_dict(self) -> dict:
        """
        示例：
        {'bulge_display': 0, 'emoticon_unique': 'official_13', 'height': 60, 'in_player_area': 1, 'is_dynamic': 1,
         'url': 'https://i0.hdslb.com/bfs/live/a98e35996545509188fe4d24bd1a56518ea5af48.png', 'width': 183}
        """
        if isinstance(self.emoticon_options, dict):
            return self.emoticon_options
        try:
            return json.loads(self.emoticon_options)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def voice_config_dict(self) -> dict:
        """
        示例：
        {'voice_url': 'https%3A%2F%2Fboss.hdslb.com%2Flive-dm-voice%2Fb5b26e48b556915cbf3312a59d3bb2561627725945.wav
         %3FX-Amz-Algorithm%3DAWS4-HMAC-SHA256%26X-Amz-Credential%3D2663ba902868f12f%252F20210731%252Fshjd%252Fs3%25
         2Faws4_request%26X-Amz-Date%3D20210731T100545Z%26X-Amz-Expires%3D600000%26X-Amz-SignedHeaders%3Dhost%26
         X-Amz-Signature%3D114e7cb5ac91c72e231c26d8ca211e53914722f36309b861a6409ffb20f07ab8',
         'file_format': 'wav', 'text': '汤，下午好。', 'file_duration': 1}
        """
        if isinstance(self.voice_config, dict):
            return self.voice_config
        try:
            return json.loads(self.voice_config)
        except (json.JSONDecodeError, TypeError):
            return {}


@dataclasses.dataclass
class GiftMessage:
    """
    礼物消息
    """

    gift_name: str = ''
    """礼物名"""
    num: int = 0
    """数量"""
    uname: str = ''
    """用户名"""
    face: str = ''
    """用户头像URL"""
    guard_level: int = 0
    """舰队等级，0非舰队，1总督，2提督，3舰长"""
    uid: int = 0
    """用户ID"""
    timestamp: int = 0
    """时间戳"""
    gift_id: int = 0
    """礼物ID"""
    gift_type: int = 0
    """礼物类型（未知）"""
    action: str = ''
    """目前遇到的有'喂食'、'赠送'"""
    price: int = 0
    """礼物单价瓜子数"""
    rnd: str = ''
    """随机数，可能是去重用的。有时是时间戳+去重ID，有时是UUID"""
    coin_type: str = ''
    """瓜子类型，'silver'或'gold'，1000金瓜子 = 1元"""
    total_coin: int = 0
    """总瓜子数"""
    tid: str = ''
    """可能是事务ID，有时和rnd相同"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            gift_name=data['giftName'],
            num=data['num'],
            uname=data['uname'],
            face=data['face'],
            guard_level=data['guard_level'],
            uid=data['uid'],
            timestamp=data['timestamp'],
            gift_id=data['giftId'],
            gift_type=data['giftType'],
            action=data['action'],
            price=data['price'],
            rnd=data['rnd'],
            coin_type=data['coin_type'],
            total_coin=data['total_coin'],
            tid=data['tid'],
        )


@dataclasses.dataclass
class GuardBuyMessage:
    """
    上舰消息
    """

    uid: int = 0
    """用户ID"""
    username: str = ''
    """用户名"""
    guard_level: int = 0
    """舰队等级，0非舰队，1总督，2提督，3舰长"""
    num: int = 0
    """数量"""
    price: int = 0
    """单价金瓜子数"""
    gift_id: int = 0
    """礼物ID"""
    gift_name: str = ''
    """礼物名"""
    start_time: int = 0
    """开始时间戳，和结束时间戳相同"""
    end_time: int = 0
    """结束时间戳，和开始时间戳相同"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            uid=data['uid'],
            username=data['username'],
            guard_level=data['guard_level'],
            num=data['num'],
            price=data['price'],
            gift_id=data['gift_id'],
            gift_name=data['gift_name'],
            start_time=data['start_time'],
            end_time=data['end_time'],
        )


@dataclasses.dataclass
class SuperChatMessage:
    """
    醒目留言消息
    """

    price: int = 0
    """价格（人民币）"""
    message: str = ''
    """消息"""
    message_trans: str = ''
    """消息日文翻译（目前只出现在SUPER_CHAT_MESSAGE_JPN）"""
    start_time: int = 0
    """开始时间戳"""
    end_time: int = 0
    """结束时间戳"""
    time: int = 0
    """剩余时间（约等于 结束时间戳 - 开始时间戳）"""
    id: int = 0
    """醒目留言ID，删除时用"""
    gift_id: int = 0
    """礼物ID"""
    gift_name: str = ''
    """礼物名"""
    uid: int = 0
    """用户ID"""
    uname: str = ''
    """用户名"""
    face: str = ''
    """用户头像URL"""
    guard_level: int = 0
    """舰队等级，0非舰队，1总督，2提督，3舰长"""
    user_level: int = 0
    """用户等级"""
    background_bottom_color: str = ''
    """底部背景色，'#rrggbb'"""
    background_color: str = ''
    """背景色，'#rrggbb'"""
    background_icon: str = ''
    """背景图标"""
    background_image: str = ''
    """背景图URL"""
    background_price_color: str = ''
    """背景价格颜色，'#rrggbb'"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            price=data['price'],
            message=data['message'],
            message_trans=data['message_trans'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            time=data['time'],
            id=data['id'],
            gift_id=data['gift']['gift_id'],
            gift_name=data['gift']['gift_name'],
            uid=data['uid'],
            uname=data['user_info']['uname'],
            face=data['user_info']['face'],
            guard_level=data['user_info']['guard_level'],
            user_level=data['user_info']['user_level'],
            background_bottom_color=data['background_bottom_color'],
            background_color=data['background_color'],
            background_icon=data['background_icon'],
            background_image=data['background_image'],
            background_price_color=data['background_price_color'],
        )


@dataclasses.dataclass
class SuperChatDeleteMessage:
    """
    删除醒目留言消息
    """

    ids: List[int] = dataclasses.field(default_factory=list)
    """醒目留言ID数组"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            ids=data['ids'],
        )
