import requests  # 发送请求
import pandas as pd  # 保存csv文件
import os  # 判断文件是否存在
import time
from time import sleep  # 设置等待，防止反爬
import random

# 请求头
headers = {
    "authority": "api.bilibili.com",
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    # 需定期更换cookie，否则location爬不到
    "cookie": "需换成自己的cookie值",
    "origin": "https://www.bilibili.com",
    "referer": "https://www.bilibili.com/video/BV1FG4y1Z7po/?spm_id_from=333.337.search-card.all.click&vd_source=69a50ad969074af9e79ad13b34b1a548",
    "sec-ch-ua": '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47",
}


def trans_date(v_timestamp):
    """10位时间戳转换为时间字符串"""
    timeArray = time.localtime(v_timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


response = requests.get(
    "https://www.bilibili.com/video/BV1rY4y1y7r9",
    headers=headers,
)

data_list = response.json()["data"]["replies"]

comment_list = []  # 评论内容空列表
# 循环爬取每一条评论数据
for a in data_list:
    # 评论内容
    comment = a["content"]["message"]
    comment_list.append(comment)

# 把列表拼装为DataFrame数据
df = pd.DataFrame(
    {
        "视频链接": "https://www.bilibili.com/video/" + v_bid,
        "评论页码": (i + 1),
        "评论作者": user_list,
        "评论时间": time_list,
        "IP属地": location_list,
        "点赞数": like_list,
        "评论内容": comment_list,
    }
)
# 把评论数据保存到csv文件
df.to_csv(outfile, mode="a+", encoding="utf_8_sig", index=False, header=header)
