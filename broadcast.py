import json
import logging
import random
import re
import threading
import time
import requests
from my_fake_useragent import UserAgent

logging.basicConfig(filename='steam_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - %(levelname)s : %(message)s')

# steam api
STEAM_API_URL = "https://api.steampowered.com"
# steam 社区
STEAM_COMMUNITY_URL = "https://steamcommunity.com"
# 直播间ID
STEAM_ID = "76561199476796290"

# 每个观众心跳次数，30s/次
HEARTBEAT_COUNT = 30
# 伪装的观众数量
VIEWER_COUNT = 200
# 需达到的总观众数
TOTAL_VIEWER_COUNT = 2500
# 当前观众数
CURREN_VIEWER_COUNT = 0


# 进入直播间并获取session_id
def get_session_id(user_agent: str) -> str:
    session_id = ""
    url = f"{STEAM_COMMUNITY_URL}/broadcast/watch/{STEAM_ID}"
    headers = {
        "User-Agent": user_agent,
        'Referer': STEAM_COMMUNITY_URL
    }
    response = requests.get(url, headers=headers)
    if response is None:
        logging.error(f"获取session_id异常：{response}")
        return ""
    match = re.search(r'g_sessionID\s*=\s*"([^"]+)"', response.text)
    if match:
        session_id = match.group(1)
    return session_id


# 获取直播间核心信息
def get_broadcast_mpd(session_id: str, user_agent: str) -> tuple:
    url = f"{STEAM_COMMUNITY_URL}/broadcast/getbroadcastmpd"
    params = {
        "steamid": STEAM_ID,
        "broadcastid": "0",
        "viewertoken": "",
        "watchlocation": "5",
        "sessionid": session_id
    }
    headers = {
        'Referer': f"{STEAM_COMMUNITY_URL}/broadcast/watch/{STEAM_ID}",
        "User-Agent": user_agent
    }
    response = requests.get(url, headers=headers, params=params)
    if response is None or response.text is None or response.status_code == 403:
        logging.error(f"请求response异常：{response}")
        return "", ""
    try:
        data = json.loads(response.text)
    except ValueError:
        logging.error(f"请求response异常：{response}")
        return "", ""
    broadcast_id = data["broadcastid"]
    viewer_token = data["viewertoken"]
    return broadcast_id, viewer_token


# 获取直播间观众数
def get_broadcast_info(user_agent: str, broadcast_id: str) -> None:
    url = f"{STEAM_COMMUNITY_URL}/broadcast/getbroadcastinfo"
    params = {
        "steamid": STEAM_ID,
        "broadcastid": broadcast_id,
        "watchlocation": "5"
    }
    headers = {
        'Referer': f"{STEAM_COMMUNITY_URL}/broadcast/watch/{STEAM_ID}",
        "User-Agent": user_agent
    }
    response = requests.get(url, headers=headers, params=params)
    if response is None:
        logging.error(f"请求response异常：{response}")
        return
    try:
        data = json.loads(response.text)
    except ValueError:
        logging.error(f"请求response异常：{response}")
        return
    global CURREN_VIEWER_COUNT
    CURREN_VIEWER_COUNT = data["viewer_count"]


# 轮询心跳
def heartbeat(broadcast_id: str, viewer_token: str, user_agent: str) -> None:
    data = {
        "steamid": STEAM_ID,
        "broadcastid": broadcast_id,
        "viewertoken": viewer_token
    }
    url = f"{STEAM_COMMUNITY_URL}/broadcast/heartbeat/"
    headers = {
        'Referer': f"{STEAM_COMMUNITY_URL}/broadcast/watch/{STEAM_ID}",
        "User-Agent": user_agent
    }
    count = 1
    error_count = 0
    while count <= HEARTBEAT_COUNT:
        time.sleep(30)
        try:
            response = requests.post(url, headers=headers, data=data)
            logging.debug("发送心跳响应：%s" % response)
            if response.status_code == 403:
                error_count = error_count + 1
        except Exception as e:
            logging.error("发送心跳异常：%s" % e)
            # 异常次数达到5次，停止该线程的心跳
            error_count = error_count + 1
            if error_count >= 5:
                logging.error("心跳异常次数达到5次，准备停止当前线程")
                count = HEARTBEAT_COUNT
        count = count + 1
    logging.info(f"当前线程心跳结束")


# 进入直播间并保持心跳的核心逻辑
def step() -> None:
    try:
        agent_family = ['chrome', 'firefox', 'edge']
        family = agent_family[random.randint(0, 2)]
        user_agent = UserAgent(family=family, os_family='windows').random()
        logging.debug(f"获取到UserAgent:{user_agent}")

        # 1.获取session_id
        session_id = get_session_id(user_agent)
        if len(session_id) == 0:
            logging.error("当前线程，当前任务获取session_id失败，已提前停止")
            return
        logging.debug(f"获取到session_id:{session_id}")

        # 2.获取broadcast_id、viewer_token
        broadcast_id, viewer_token = get_broadcast_mpd(session_id, user_agent)
        if len(broadcast_id) == 0 or len(viewer_token) == 0:
            logging.error("当前线程，当前任务获取broadcast_id或viewer_token失败，已提前停止")
            return
        logging.debug(f"获取到broadcast_id:{broadcast_id},viewer_token:{viewer_token}")

        # 3.刷新在线人数
        get_broadcast_info(user_agent, broadcast_id)

        # 4.轮询心跳
        heartbeat(broadcast_id, viewer_token, user_agent)
    except Exception as e:
        logging.error("当前线程任务发生异常：%s" % e)
    # 5.心跳结束获取新的会话
    logging.info(f"开始下一轮会话")
    step()


# 入口函数
def main():
    count = 1
    while count < VIEWER_COUNT:
        logging.info(f"当前在线观众数：{CURREN_VIEWER_COUNT}")
        logging.info(f"创建新线程Thread-{count}")
        t = threading.Thread(target=step, name=f'Thread-{count}')
        t.start()
        # 间隔时间随机
        time.sleep(random.randint(3, 5))
        count = count + 1


main()
