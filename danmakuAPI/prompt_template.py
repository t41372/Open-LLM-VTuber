# prompt_template.py

def danmaku_prompt(message_type, username, content):
    """
    构建指导LLM回复弹幕和打赏的内容

    :param message_type: 消息类型，可以是 'danmaku', 'gift', 'super_chat'
    :param username: 用户名
    :param content: 消息内容
    :return: 构建好的提示内容
    """
    if message_type == 'danmaku':
        return f"弹幕：{username} 说：{content}"
    elif message_type == 'gift':
        return f"{username} 赠送了礼物：{content}"
    elif message_type == 'super_chat':
        return f"{username} 发送了醒目留言：{content}"
    else:
        return f"{username} 发送了消息：{content}"