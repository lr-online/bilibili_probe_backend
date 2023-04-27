import base64
import re
from typing import List

import aiohttp
import asyncio
import json

import jieba
from loguru import logger
import xml.etree.ElementTree as ET
from pyecharts.charts import WordCloud
from pyecharts import options as opts
from collections import Counter
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot as driver


def extract_bv_number(url: str):
    # https://www.bilibili.com/video/BV1Qz411q7tg/?spm_id_from=333.337.search-card.all.click
    pattern = r"\/(BV\w+)[\/?]"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None


async def fetch_bilibili_video_info(bvid):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                resp = await response.json()
                return resp["data"]
            else:
                return None


async def download_bilibili_danmaku(cid):
    url = f"https://comment.bilibili.com/{cid}.xml"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                danmaku = await response.text()
                return danmaku
            else:
                return None


def parse_bilibili_danmaku(danmaku):
    root = ET.fromstring(danmaku)
    result = []
    for d in root.findall("./d"):
        # 解析弹幕的时间、类型、颜色和文本
        p = d.attrib["p"].split(",")
        time = float(p[0])
        danmaku_type = int(p[1])
        color = int(p[3])
        text = d.text.strip()
        # 将解析结果封装为一个字典
        danmaku_dict = {
            "time": time,
            "type": danmaku_type,
            "color": color,
            "text": text,
        }
        result.append(danmaku_dict)
    return result


def generate_wordcloud_image(
    text_list: List[str],
    title="Bilibili弹幕词云图",
):
    # 获取所有弹幕的文本内容并统计出现次数
    stopwords = set()
    with open("stopwords.txt", "r", encoding="utf-8") as f:
        for line in f:
            stopwords.add(line.strip())

    words = jieba.lcut(" ".join(text_list))

    word_counts = Counter()
    for w in words:
        if w not in stopwords and len(w) > 1:
            word_counts[w] += 1
    word_counts_top50 = word_counts.most_common(500)

    # 将数据转换为pyecharts词云图需要的格式
    wordcloud_data = [(word, count) for word, count in word_counts_top50]

    # 使用pyecharts库绘制词云图
    wordcloud = WordCloud()
    wordcloud.add("", wordcloud_data, word_size_range=[20, 100], shape="circle")
    wordcloud.set_global_opts(title_opts=opts.TitleOpts(title=title))
    # wordcloud_html_path = f"./wordcloud_cache/{title}.html"
    # wordcloud.render(wordcloud_html_path)  # 生成HTML文件
    # logger.info(f"生成的词云图已保存为HTML文件：{wordcloud_html_path}")

    # 使用pyecharts-snapshot库将词云图保存为图片
    wordcloud_png_path = f"./wordcloud_cache/{title}.png"
    make_snapshot(driver, wordcloud.render(), wordcloud_png_path)
    logger.info(f"生成的词云图已保存为PNG文件：{wordcloud_png_path}")
    with open(wordcloud_png_path, "rb") as f:
        return base64.b64encode(f.read())


async def download_bilibili_comments(bv_number):
    url = f"https://api.bilibili.com/x/v2/reply?jsonp=jsonp&pn=1&type=1&oid={bv_number}&sort=0"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response_text = await resp.text()
            response_dict = json.loads(response_text)
            comments = response_dict["data"]["replies"]
            return comments


async def bv_probe(video_url: str):
    bv_number = extract_bv_number(video_url)
    assert bv_number, f"无法从URL {video_url} 中解析到视频bv号 "

    logger.info(f"URL {video_url} 中解析到视频bv号是 {bv_number}")
    video_info = await fetch_bilibili_video_info(bv_number)
    assert video_info, f"获取视频 {bv_number} 的详情失败"
    logger.info(video_info)

    cid = video_info["cid"]
    danmaku_xml = await download_bilibili_danmaku(cid)
    assert danmaku_xml, f"获取视频 {bv_number} 的弹幕失败"
    danmaku_json = parse_bilibili_danmaku(danmaku_xml)
    logger.info(f"视频 {bv_number} 的弹幕 {danmaku_json}")

    comments = await download_bilibili_comments(bv_number)
    logger.info(f"视频 {bv_number} 的评论 {comments}")

    danmaku_wordcloud = generate_wordcloud_image(
        (d["text"] for d in danmaku_json),
        title=video_info["title"] + "——弹幕词云",
    )
    comments_wordcloud = generate_wordcloud_image(
        (comment["content"]["message"] for comment in comments),
        title=video_info["title"] + "——评论词云",
    )
    return {
        "bv_number": bv_number,
        "owner_name": video_info["owner"]["name"],
        "owner_avatar": video_info["owner"]["face"],
        "pubdate": video_info["pubdate"],  # 秒级时间戳
        "cover": video_info["pic"],
        "title": video_info["title"],
        "duration": video_info["duration"],  # 视频时长，秒
        "like": video_info["stat"]["like"],  # 点赞数
        "coin": video_info["stat"]["coin"],  # 投币数
        "favorite": video_info["stat"]["favorite"],  # 收藏
        "share": video_info["stat"]["share"],  # 分享数
        "danmaku_wordcloud": danmaku_wordcloud,
        "comments_wordcloud": comments_wordcloud,
        "danmaku": danmaku_json,
        "comments": comments,
    }


if __name__ == "__main__":
    url = "https://www.bilibili.com/video/BV1tT411n7Nd/?spm_id_from=333.1073.high_energy.content.click&vd_source=106bf7a07b011cc5dee54dccd3ae29f0"
    asyncio.run(bv_probe(url))
