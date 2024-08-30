from selenium import webdriver
from bs4 import BeautifulSoup
import time
import os
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {msg}')

def search_douyin_videos(keyword):
    driver = webdriver.Chrome()
    driver.get(f"https://www.douyin.com/search/{keyword}")
    
    try:
        # 打印当前页面的标题，确认页面是否正确加载
        print(f"页面标题：{driver.title}")
        # 等待搜索结果中的视频元素加载完成
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'search-video-item'))
        )
    except Exception as e:
        print(f"等待元素加载时出错: {e}")
        driver.quit()
        return []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    videos = []

    for video in soup.find_all('div', class_='search-video-item'):
        try:
            link = video.find('a')['href']
            if not link.startswith('http'):
                link = "https://www.douyin.com" + link
            print(f"视频链接：{link}")
            likes_text = video.find('span', class_='like-count').text
            if 'w' in likes_text:
                likes = int(float(likes_text.replace('w', '')) * 10000)
            else:
                likes = int(likes_text)
            print(f"点赞数：{likes}")
            videos.append({'link': link, 'likes': likes})
        except Exception as e:
            print(f"解析错误：{e}")

    driver.quit()
    return videos

def download_video(video_url):
    print(f"下载视频链接：{video_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }
    response = requests.get(video_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_link = video_tag['src']
            print(f"视频文件链接：{video_link}")
            video_id = video_url.split('/')[-1]
            video_path = os.path.join("D:\\code\\tiktok\\video", f"{video_id}.mp4")
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            video_response = requests.get(video_link, stream=True)
            if video_response.status_code == 200:
                with open(video_path, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f'视频 {video_id} 下载成功')
                return video_path
            else:
                print('下载视频失败')
        else:
            print('未找到视频文件链接')
    else:
        print('获取页面失败')

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
                'tags': ['抖音', '上传'],
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
    keyword = "小杨哥"  # 修改关键词以获取不同视频
    videos = search_douyin_videos(keyword)
    
    # 过滤出点赞量最高的前3个视频
    top_videos = sorted(videos, key=lambda x: x['likes'], reverse=True)[:3]
    
    for video in top_videos:
        video_path = download_video(video['link'])
        if video_path:
            upload_to_youtube(video_path, '自动上传的抖音视频')
