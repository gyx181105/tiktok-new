import os
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# 设置API范围
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
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

        # 设置视频文件路径和视频元数据
        video_file = 'D:/code/tiktok/video/7406304553181744404.mp4'
        body = {
            'snippet': {
                'title': '测试上传视频',
                'description': '通过YouTube Data API v3上传的视频',
                'tags': ['测试', 'API'],
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
    main()