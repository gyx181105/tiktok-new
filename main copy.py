import datetime
import time
import os
from DrissionPage import ChromiumPage, ChromiumOptions
import random
import json
from selenium.webdriver.common.by import By # type: ignore


def print_msg(msg):
    print(f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}')


def init_page_and_tabs():
    co = ChromiumOptions(read_file=False)
    co.use_system_user_path()
    co.set_local_port(9222)
    co.set_argument('--start-maximized')
    co.set_timeouts(30, 30, 30)
    co.set_retry(5, 5)
    p = ChromiumPage(addr_or_opts=co)

    # 获取所有打开的标签页
    tabs = p.get_tabs()
    tab_1 = None
    tab_2 = None

    # 查找是否有已打开的抖音标签页
    for tab in tabs:
        if 'douyin.com' in tab.url:
            tab_1 = tab
        elif 'youtube.com' in tab.url:
            tab_2 = tab

    # 如果没有找到，就新建一个
    if not tab_1:
        tab_1 = p.new_tab('https://www.tiktok.com/')
    if not tab_2:
        tab_2 = p.new_tab('https://studio.youtube.com/')

    return p, tab_1, tab_2


def post_video(id, desc):
    print_msg('正在上传视频：' + id + '.mp4')

    if len(desc) == 0:
        desc = 'a nice video'
    if len(desc) > 100:
        desc = desc[:100]

    tab_youtube.get('https://studio.youtube.com/')
    tab_youtube.wait(10)  # 增加等待时间

    tab_youtube.ele('tag=ytcp-button@id=create-icon').click()
    tab_youtube.wait(5)

    tab_youtube.ele('tag=tp-yt-paper-item@id=text-item-0').click()
    tab_youtube.wait(5)

    video_path1 = os.path.join('D:\\code\\tiktok\\video', id + '.mp4')
    print('video_path1:', video_path1)

    # 增加查找文件输入框的等待时间
    file_input = tab_youtube.ele('input[type="file"]', timeout=10)
    if file_input:
        file_input.set_value(video_path1)
    else:
        print_msg("未能找到文件上传输入框")
        return  # 如果找不到文件输入框，停止函数执行

    tab_youtube.wait(5)

    # 输入视频描述
    textbox_element = tab_youtube.ele('tag=div@@id=textbox@@slot=input', timeout=10)
    if textbox_element:
        textbox_element.input(desc)
    else:
        print_msg("未能找到文本框")
        return  # 如果找不到文本框，停止函数执行

    tab_youtube.wait(5)

    for _ in range(3):
        tab_youtube.ele('tag=ytcp-button@id=next-button').click()
        tab_youtube.wait(5)

    tab_youtube.ele('tag=ytcp-button@id=done-button').click()
    tab_youtube.wait(5)

    print_msg(id + '.mp4' + "上传成功")






def loop_function():
    tab_tiktok.listen.start('https://www.tiktok.com/api/post/item_list')
    tab_tiktok.get(user_main_page)
    res = tab_tiktok.listen.wait(timeout=30)
    tab_tiktok.listen.stop()
    if res:
        if not res.is_failed:
            if isinstance(res.response.body, dict):
                try:
                    itemList = res.response.body["itemList"]
                    for dic in itemList:
                        createTime = dic['createTime']
                        id = dic['id']
                        # create_time > start_time, aweme_id not in posted_list, media_type  == 4
                        if createTime < start_time and id not in posted_list:
                            # 获取视频链接，并下载
                            playAddr = dic['video']['playAddr']
                            print(playAddr)
                            path = os.path.join(os.getcwd(), "video")
                            d_r = tab_tiktok.download(file_url=playAddr, rename=id, suffix='mp4', goal_path=path,
                                                      file_exists='overwrite')
                            if d_r[0] == 'success':
                                # 调用发布函数
                                desc = dic['desc']
                                post_video(id, desc)
                                posted_list.append(id)
                            else:
                                print_msg('下载视频失败')
                except KeyError:
                    print_msg("The key 'itemList' does not exist in the dictionary")
            else:
                print_msg("The response body is not a dictionary")
        else:
            print_msg("Failed to get response")
    else:
        print_msg("Waited for 30 seconds but no response was received")


if __name__ == '__main__':
    user_main_page = input('请输入目标用户主页链接：\n')

    page, tab_tiktok, tab_youtube = init_page_and_tabs()

    start_time = int(time.time())
    posted_list = []

    index = 1
    while True:
        print_msg(f'第{index}次检查~')
        index += 1
        loop_function()

        time.sleep(random.randint(30, 60))