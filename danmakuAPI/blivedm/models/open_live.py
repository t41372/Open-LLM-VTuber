# -*- coding: utf-8 -*-
import dataclasses
from typing import *

__all__ = (
    'DanmakuMessage',
    'GiftMessage',
    'GuardBuyMessage',
    'SuperChatMessage',
    'SuperChatDeleteMessage',
    'LikeMessage',
)

# 注释都是复制自官方文档的，看不懂的话问B站
# https://open-live.bilibili.com/document/f9ce25be-312e-1f4a-85fd-fef21f1637f8


@dataclasses.dataclass
class DanmakuMessage:
    """
    弹幕消息
    """

    uname: str = ''
    """用户昵称"""
    open_id: str = ''
    """用户唯一标识"""
    uface: str = ''
    """用户头像"""
    timestamp: int = 0
    """弹幕发送时间秒级时间戳"""
    room_id: int = 0
    """弹幕接收的直播间"""
    msg: str = ''
    """弹幕内容"""
    msg_id: str = ''
    """消息唯一id"""
    guard_level: int = 0
    """对应房间大航海等级"""
    fans_medal_wearing_status: bool = False
    """该房间粉丝勋章佩戴情况"""
    fans_medal_name: str = ''
    """粉丝勋章名"""
    fans_medal_level: int = 0
    """对应房间勋章信息"""
    emoji_img_url: str = ''
    """表情包图片地址"""
    dm_type: int = 0
    """弹幕类型 0：普通弹幕 1：表情包弹幕"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            uname=data['uname'],
            open_id=data['open_id'],
            uface=data['uface'],
            timestamp=data['timestamp'],
            room_id=data['room_id'],
            msg=data['msg'],
            msg_id=data['msg_id'],
            guard_level=data['guard_level'],
            fans_medal_wearing_status=data['fans_medal_wearing_status'],
            fans_medal_name=data['fans_medal_name'],
            fans_medal_level=data['fans_medal_level'],
            emoji_img_url=data['emoji_img_url'],
            dm_type=data['dm_type'],
        )


@dataclasses.dataclass
class AnchorInfo:
    """
    主播信息
    """

    uid: int = 0
    """收礼主播uid"""
    open_id: str = ''
    """收礼主播唯一标识"""
    uname: str = ''
    """收礼主播昵称"""
    uface: str = ''
    """收礼主播头像"""

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            uid=data['uid'],
            open_id=data['open_id'],
            uname=data['uname'],
            uface=data['uface'],
        )


@dataclasses.dataclass
class ComboInfo:
    """
    连击信息
    """

    combo_base_num: int = 0
    """每次连击赠送的道具数量"""
    combo_count: int = 0
    """连击次数"""
    combo_id: str = ''
    """连击id"""
    combo_timeout: int = 0
    """连击有效期秒"""

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            combo_base_num=data['combo_base_num'],
            combo_count=data['combo_count'],
            combo_id=data['combo_id'],
            combo_timeout=data['combo_timeout'],
        )


@dataclasses.dataclass
class GiftMessage:
    """
    礼物消息
    """

    room_id: int = 0
    """房间号"""
    open_id: str = ''
    """用户唯一标识"""
    uname: str = ''
    """送礼用户昵称"""
    uface: str = ''
    """送礼用户头像"""
    gift_id: int = 0
    """道具id(盲盒:爆出道具id)"""
    gift_name: str = ''
    """道具名(盲盒:爆出道具名)"""
    gift_num: int = 0
    """赠送道具数量"""
    price: int = 0
    """礼物爆出单价，(1000 = 1元 = 10电池),盲盒:爆出道具的价值"""
    paid: bool = False
    """是否是付费道具"""
    fans_medal_level: int = 0
    """实际送礼人的勋章信息"""
    fans_medal_name: str = ''
    """粉丝勋章名"""
    fans_medal_wearing_status: bool = False
    """该房间粉丝勋章佩戴情况"""
    guard_level: int = 0
    """大航海等级"""
    timestamp: int = 0
    """收礼时间秒级时间戳"""
    anchor_info: AnchorInfo = dataclasses.field(default_factory=AnchorInfo)
    """主播信息"""
    msg_id: str = ''
    """消息唯一id"""
    gift_icon: str = ''
    """道具icon"""
    combo_gift: bool = False
    """是否是combo道具"""
    combo_info: ComboInfo = dataclasses.field(default_factory=ComboInfo)
    """连击信息"""

    @classmethod
    def from_command(cls, data: dict):
        combo_info = data.get('combo_info', None)
        if combo_info is None:
            combo_info = ComboInfo()
        else:
            combo_info = ComboInfo.from_dict(combo_info)

        return cls(
            room_id=data['room_id'],
            open_id=data['open_id'],
            uname=data['uname'],
            uface=data['uface'],
            gift_id=data['gift_id'],
            gift_name=data['gift_name'],
            gift_num=data['gift_num'],
            price=data['price'],
            paid=data['paid'],
            fans_medal_level=data['fans_medal_level'],
            fans_medal_name=data['fans_medal_name'],
            fans_medal_wearing_status=data['fans_medal_wearing_status'],
            guard_level=data['guard_level'],
            timestamp=data['timestamp'],
            anchor_info=AnchorInfo.from_dict(data['anchor_info']),
            msg_id=data['msg_id'],
            gift_icon=data['gift_icon'],
            combo_gift=data.get('combo_gift', False),  # 官方的调试工具没发这个字段
            combo_info=combo_info,  # 官方的调试工具没发这个字段
        )


@dataclasses.dataclass
class UserInfo:
    """
    用户信息
    """

    open_id: str = ''
    """用户唯一标识"""
    uname: str = ''
    """用户昵称"""
    uface: str = ''
    """用户头像"""

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            open_id=data['open_id'],
            uname=data['uname'],
            uface=data['uface'],
        )


@dataclasses.dataclass
class GuardBuyMessage:
    """
    上舰消息
    """

    user_info: UserInfo = dataclasses.field(default_factory=UserInfo)
    """用户信息"""
    guard_level: int = 0
    """大航海等级"""
    guard_num: int = 0
    """大航海数量"""
    guard_unit: str = ''
    """大航海单位"""
    price: int = 0
    """大航海金瓜子"""
    fans_medal_level: int = 0
    """粉丝勋章等级"""
    fans_medal_name: str = ''
    """粉丝勋章名"""
    fans_medal_wearing_status: bool = False
    """该房间粉丝勋章佩戴情况"""
    room_id: int = 0
    """房间号"""
    msg_id: str = ''
    """消息唯一id"""
    timestamp: int = 0
    """上舰时间秒级时间戳"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            user_info=UserInfo.from_dict(data['user_info']),
            guard_level=data['guard_level'],
            guard_num=data['guard_num'],
            guard_unit=data['guard_unit'],
            price=data['price'],
            fans_medal_level=data['fans_medal_level'],
            fans_medal_name=data['fans_medal_name'],
            fans_medal_wearing_status=data['fans_medal_wearing_status'],
            room_id=data['room_id'],
            msg_id=data['msg_id'],
            timestamp=data['timestamp'],
        )


@dataclasses.dataclass
class SuperChatMessage:
    """
    醒目留言消息
    """

    room_id: int = 0
    """直播间id"""
    open_id: str = ''
    """用户唯一标识"""
    uname: str = ''
    """购买的用户昵称"""
    uface: str = ''
    """购买用户头像"""
    message_id: int = 0
    """留言id(风控场景下撤回留言需要)"""
    message: str = ''
    """留言内容"""
    rmb: int = 0
    """支付金额(元)"""
    timestamp: int = 0
    """赠送时间秒级"""
    start_time: int = 0
    """生效开始时间"""
    end_time: int = 0
    """生效结束时间"""
    guard_level: int = 0
    """对应房间大航海等级"""
    fans_medal_level: int = 0
    """对应房间勋章信息"""
    fans_medal_name: str = ''
    """对应房间勋章名字"""
    fans_medal_wearing_status: bool = False
    """该房间粉丝勋章佩戴情况"""
    msg_id: str = ''
    """消息唯一id"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            room_id=data['room_id'],
            open_id=data['open_id'],
            uname=data['uname'],
            uface=data['uface'],
            message_id=data['message_id'],
            message=data['message'],
            rmb=data['rmb'],
            timestamp=data['timestamp'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            guard_level=data['guard_level'],
            fans_medal_level=data['fans_medal_level'],
            fans_medal_name=data['fans_medal_name'],
            fans_medal_wearing_status=data['fans_medal_wearing_status'],
            msg_id=data['msg_id'],
        )


@dataclasses.dataclass
class SuperChatDeleteMessage:
    """
    删除醒目留言消息
    """

    room_id: int = 0
    """直播间id"""
    message_ids: List[int] = dataclasses.field(default_factory=list)
    """留言id"""
    msg_id: str = ''
    """消息唯一id"""

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            room_id=data['room_id'],
            message_ids=data['message_ids'],
            msg_id=data['msg_id'],
        )


@dataclasses.dataclass
class LikeMessage:
    """
    点赞消息

    请注意：用户端每分钟触发若干次的情况下只会推送一次该消息
    """

    uname: str = ''
    """用户昵称"""
    open_id: str = ''
    """用户唯一标识"""
    uface: str = ''
    """用户头像"""
    timestamp: int = 0
    """时间秒级时间戳"""
    room_id: int = 0
    """发生的直播间"""
    like_text: str = ''
    """点赞文案(“xxx点赞了”)"""
    like_count: int = 0
    """对单个用户最近2秒的点赞次数聚合"""
    fans_medal_wearing_status: bool = False
    """该房间粉丝勋章佩戴情况"""
    fans_medal_name: str = ''
    """粉丝勋章名"""
    fans_medal_level: int = 0
    """对应房间勋章信息"""
    msg_id: str = ''  # 官方文档表格里没列出这个字段，但是参考JSON里面有
    """消息唯一id"""
    # 还有个guard_level，但官方文档没有出现这个字段，就不添加了

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            uname=data['uname'],
            open_id=data['open_id'],
            uface=data['uface'],
            timestamp=data['timestamp'],
            room_id=data['room_id'],
            like_text=data['like_text'],
            like_count=data['like_count'],
            fans_medal_wearing_status=data['fans_medal_wearing_status'],
            fans_medal_name=data['fans_medal_name'],
            fans_medal_level=data['fans_medal_level'],
            msg_id=data.get('msg_id', ''),  # 官方文档表格里没列出这个字段，但是参考JSON里面有
        )
