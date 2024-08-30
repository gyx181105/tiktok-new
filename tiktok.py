import datetime
import time
import os
import random
import requests
import re
from DrissionPage import ChromiumPage, ChromiumOptions
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# 设置YouTube API的范围
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def print_msg(msg):
    # 打印带有时间戳的消息
    print(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}')

def init_page_and_tabs():
    # 初始化 Chromium 浏览器配置
    co = ChromiumOptions(read_file=False)  # 创建 Chromium 浏览器选项对象，禁止读取配置文件
    co.use_system_user_path()  # 使用系统默认的用户路径
    co.set_local_port(9222)  # 设置本地调试端口为 9222
    co.set_argument('--start-maximized')  # 浏览器启动时最大化
    co.set_timeouts(30, 30, 30)  # 设置页面加载和元素查找的超时时间
    co.set_retry(5, 5)  # 设置请求重试次数和间隔
    p = ChromiumPage(addr_or_opts=co)  # 启动 Chromium 浏览器

    # 初始化 TikTok 选项卡
    tab_1 = None
    tab_1_id = p.get_tabs(url='tiktok.com')  # 查找已经打开的 TikTok 页面
    if tab_1_id:
        tab_1 = p.get_tab(tab_1_id)  # 获取已存在的 TikTok 选项卡
    else:
        tab_1 = p.new_tab('https://www.tiktok.com/')  # 创建新选项卡并打开 TikTok

    return p, tab_1  # 只返回浏览器页面对象和 TikTok 选项卡

def loop_function():
    # 主循环函数，负责从 TikTok 获取视频并下载
    tab_tiktok.listen.start('https://www.tiktok.com/api/post/item_list')  # 开始监听 TikTok API 请求
    tab_tiktok.get(user_main_page)  # 访问用户主页
    res = tab_tiktok.listen.wait(timeout=30)  # 等待 API 请求返回
    tab_tiktok.listen.stop()  # 停止监听

    if res:
        if not res.is_failed:
            if isinstance(res.response.body, dict):
                try:
                    itemList = res.response.body["itemList"]  # 获取视频列表
                    for dic in itemList:
                        createTime = dic['createTime']
                        id = dic['id']
                        # 过滤符合条件的视频
                        if createTime > start_time and id not in posted_list:
                            # 获取视频链接并下载
                            playAddr = dic['video']['playAddr']
                            print(playAddr)
                            path = os.path.join(os.getcwd(), "video")  # 设置视频保存路径
                            d_r = tab_tiktok.download(file_url=playAddr, rename=id, suffix='mp4', goal_path=path, file_exists='overwrite')
                            if d_r[0] == 'success':
                                print_msg(f'视频 {id}.mp4 下载成功')
                                posted_list.append(id)  # 将视频 ID 添加到已下载列表
                                
                                # 下载成功后自动上传到 YouTube
                                upload_to_youtube(os.path.join(path, f"{id}.mp4"), dic['desc'])
                            else:
                                print_msg('下载视频失败')
                except KeyError:
                    print_msg("The key 'itemList' does not exist in the dictionary")  # 异常处理：找不到视频列表
            else:
                print_msg("The response body is not a dictionary")  # 异常处理：返回体不是字典
        else:
            print_msg("Failed to get response")  # 异常处理：请求失败
    else:
        print_msg("Waited for 30 seconds but no response was received")  # 异常处理：超时无响应

def upload_to_youtube(video_file, description):
    creds = None

    # 检查是否已保存用户的凭据
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # 如果没有保存凭据，或者凭据无效，进行OAuth 2.0流程
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 将凭据保存到文件
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # 使用凭据构建YouTube API客户端
        youtube = build('youtube', 'v3', credentials=creds)

        # 设置视频元数据
        body = {
            'snippet': {
                'title': '自动上传的视频',
                'description': description,
                'tags': ['自动', '上传', 'TikTok'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'private'
            }
        }

        # 创建MediaFileUpload对象
        media = MediaFileUpload(video_file, chunksize=-1, resumable=True)

        # 执行上传请求
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f'上传进度：{int(status.progress() * 100)}%')

        print('上传完成，视频ID：', response['id'])

    except HttpError as e:
        print(f'发生错误：{e}')

if __name__ == '__main__':
    # 主程序入口
    user_main_page = input('请输入目标用户主页链接：\n')  # 输入目标用户主页链接

    page, tab_tiktok = init_page_and_tabs()  # 初始化页面和选项卡

    start_time = int(time.time())  # 设置开始时间戳
    posted_list = []  # 初始化已下载视频列表

    index = 1
    while True:
        print_msg(f'第{index}次检查~')  # 打印循环检查次数
        index += 1
        loop_function()  # 调用主循环函数

        time.sleep(random.randint(30, 60))  # 随机等待 30 到 60 秒
