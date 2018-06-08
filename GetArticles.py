#!/usr/bin/env python
# encoding: utf-8

"""
@file: GetArticles.py
@time: 2018/5/11 16:16
@desc: 收集简书所有专题下的文章数据
@author: hongquanpro@126.com
"""

import os
import json
import requests
import re
import logging

from jianshu.util.Mysql import Mysql

# 配置日志信息
logger = logging.getLogger()
logger.setLevel(logging.INFO)
BASIC_FORMAT = "%(asctime)s[%(levelname)s]:%(message)s"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
# 输出到控制台的 handler
chlr = logging.StreamHandler()
chlr.setFormatter(formatter)
# 也可以不设置，不设置就默认用 logger 的 level
chlr.setLevel(logging.INFO)
# 输出到文件的handler
fhlr = logging.FileHandler(os.path.join(os.getcwd(), 'article.log'))
fhlr.setFormatter(formatter)
logger.addHandler(chlr)
logger.addHandler(fhlr)
# 简单配置, 只能选择输出到控制台或文件中
# logging.basicConfig(filename=os.path.join(os.getcwd(), 'article.log'),
#                     level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s: %(message)s')

fetch_error_tag = "fetch_error"
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Cookie': 'UM_distinctid=15b89d53a930-02ab95f11ccae2-51462d15-1aeaa0-15b89d53a9489b; CNZZDATA1258679142=1544557204-1492664886-%7C1493280769; remember_user_token=W1szNDgxMjU3XSwiJDJhJDEwJDlSS3VLcFFWMlZzNFJuOFFNS1JQR3UiLCIxNDk0MjEzNDQ3LjYwODEwNzgiXQ%3D%3D--9241542a4e44d55acaf8736a1d57dd0e96ad4e7a; _ga=GA1.2.2016948485.1492666105; _gid=GA1.2.824702661.1494486429; _gat=1; Hm_lvt_0c0e9d9b1e7d617b3e6842e85b9fb068=1494213432,1494213612,1494321303,1494387194; Hm_lpvt_0c0e9d9b1e7d617b3e6842e85b9fb068=1494486429; _session_id=czl6dzVOeXdYaEplRVdndGxWWHQzdVBGTll6TVg5ZXFDTTI5cmN2RUsvS2Y2d3l6YlkrazZkZWdVcmZDSjFuM2tpMHpFVHRTcnRUVnAyeXhRSnU5UEdhaGMrNGgyMTRkeEJYOE9ydmZ4N1prN1NyekFibkQ5K0VrT3paUWE1bnlOdzJrRHRrM0Z2N3d3d3hCcFRhTWdWU0lLVGpWWjNRdjArZkx1V2J0bGJHRjZ1RVBvV25TYnBQZmhiYzNzOXE3VWNBc25YSS93WUdsTEJFSHVIck4wbVI5aWJrUXFaMkJYdW41WktJUDl6OVNqZ2k0NWpGL2dhSWx0S2FpNzhHcFZvNGdQY012QlducWgxNVhoUEN0dUpCeUI4bEd3OXhiMEE2WEplRmtaYlR6VTdlZXFsaFFZMU56M2xXcWwwbmlZeWhVb0dXKzhxdEtJaFZKaUxoZVpUZEZPSnBGWmF3anFJaFZpTU9Icm4wcllqUFhWSzFpYWF4bTZmSEZ1QXdwRWs3SHNEYmNZelA4VG5zK0wvR0MwZDdodlhZakZ6OWRVbUFmaE5JMTIwOD0tLXVyVEVSeVdOLy9Cak9nVG0zV0hueVE9PQ%3D%3D--ea401e8c501e7b749d593e1627dbaa88ab4befc2',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36',
    'Host': 'www.jianshu.com',
    "X-Requested-With": 'XMLHttpRequest'
}

# 数据库管理类
db = Mysql()


# 获取文章详情并进行入库处理
def get_article(article_id):
    url = "https://www.jianshu.com/p/%s" % article_id
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error('get_article() Response Code: %d' % response.status_code)
        exit()
        return
    html = response.text
    # 获取文章标题
    article_title = re.findall(r'<h1 class="title">(.*?)</h1>', html, re.S)
    if len(article_title) > 0:
        article_title = article_title[0]
    else:
        article_title = fetch_error_tag
    # 获取作者信息
    article_author_info = re.findall(r'<span class="name"><a href="/u/(.*?)">(.*?)</a></span>', html, re.S)
    if len(article_author_info) == 1:
        article_author_info = article_author_info[0]
        article_author_id = article_author_info[0]
        article_author_nickname = article_author_info[1]
    else:
        article_author_id = fetch_error_tag
        article_author_nickname = fetch_error_tag
    # 获取发布时间
    article_publish_time = re.findall(r'<span class="publish-time".*?>(.*?)</span>', html, re.S)
    if len(article_publish_time) > 0:
        article_publish_time = article_publish_time[0][0:-1]
    else:
        article_publish_time = "0000.00.00 00:00"
    # 获取阅读、喜欢和评论数据
    article_json_info = re.findall(r'<script type="application/json" data-name="page-data">(.*?)</script>', html, re.S)
    if len(article_json_info) == 1:
        json_obj = json.loads(article_json_info[0])
        note_obj = json_obj["note"]
        article_likes_count = note_obj.get('likes_count', -999)
        article_views_count = note_obj.get('views_count', -999)
        article_public_wordage = note_obj.get('public_wordage', -999)
        article_comments_count = note_obj.get('comments_count', -999)
        article_total_rewards_count = note_obj.get('total_rewards_count', -999)
        article_purchased_count = note_obj.get('purchased_count', -999)
        article_retail_price = note_obj.get('retail_price', -999)
        author_obj = note_obj['author']
        author_total_wordage = author_obj.get('total_wordage', -999)
        author_followers_count = author_obj.get('followers_count', -999)
        author_total_likes_count = author_obj.get('total_likes_count', -999)
    else:
        article_views_count = -99
        article_likes_count = -99
        article_public_wordage = -99
        article_comments_count = -99
        article_total_rewards_count = -99
        article_purchased_count = -99
        article_retail_price = -99
        author_total_wordage = -99
        author_followers_count = -99
        author_total_likes_count = -99
    # 保存作者数据
    rs = db.get_one('select count(id) as count from author where user_id=%s', article_author_id)
    if rs.get('count', -1) == 0:
        # 新增作者信息
        if db.insert_one(
                'insert into author(user_id,nickname,total_wordage,follower_count,likes_count) values(%s,%s,%s,%s,%s)',
                (article_author_id, article_author_nickname, author_total_wordage, author_followers_count,
                 author_total_likes_count)) > 0:
            logging.info('新增作者信息成功! [%s]%s 文字(%s) 粉丝(%s) 喜欢(%s)'
                         % (article_author_id, article_author_nickname, author_total_wordage, author_followers_count,
                            author_total_likes_count))
        else:
            logging.info('新增作者信息失败! [%s]%s' % (article_author_id, article_author_nickname))
    else:
        # 更新作者信息
        db.update('update author set nickname=%s,total_wordage=%s,follower_count=%s,likes_count=%s where user_id=%s',
                  (article_author_nickname, author_total_wordage, author_followers_count, author_total_likes_count,
                   article_author_id))
        # logging.info('更新作者信息成功! [%s]%s 文字(%s) 粉丝(%s) 喜欢(%s)'
        #       % (article_author_id, article_author_nickname, author_total_wordage, author_followers_count,
        #          author_total_likes_count))
    # 保存文章数据
    db.update('update article set title=%s,public_wordage=%s,views_count=%s,'
              'likes_count=%s,comments_count=%s,rewards_count=%s,retail_price=%s,purchased_count=%s,publish=%s where article_id=%s',
              (article_title, article_public_wordage, article_views_count, article_likes_count,
               article_comments_count, article_total_rewards_count, article_retail_price,
               article_purchased_count, article_publish_time, article_id))
    logging.info('更新文章数据成功! 作者(%s) ID(%s) 总字数(%s) 粉丝(%s) 喜欢(%s) - <%s> 字数(%s) 阅读(%s) 喜欢(%s) 评论(%s) 赞赏(%s) 价格(%s) 付费(%s)'
                 % (article_author_nickname, article_author_id, author_total_wordage, author_followers_count,
                    author_total_likes_count,
                    article_title, article_public_wordage, article_views_count, article_likes_count,
                    article_comments_count,
                    article_total_rewards_count, article_retail_price, article_purchased_count))


# 获取所有文章ID
def get_all_article(category_id, page=1):
    url = 'https://www.jianshu.com/c/%s?order_by=added_at&page=%s' % (category_id, page)
    logging.info('正在抓取 %s' % url)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.error('get_all_article() Response Code: %d' % response.status_code)
        exit()
        return
    html = response.text
    rs = re.findall(r'<a class="title" target="_blank" href="/p/(.*?)">', html, re.S)
    # 判断是否有下一页
    if len(rs) > 0:
        for id in rs:
            # 保存 ID 到数据库中
            rs = db.get_one('select count(id) as count from article where article_id=%s', id)
            if rs.get('count', -1) == 0:
                # 不存在的话就添加到数据库
                db.insert_one('insert into article(article_id) values(%s)', id) > 0
            # 获取文章信息
            get_article(article_id=id)
        # 嵌套循环
        get_all_article(category_id, page + 1)
    else:
        # 更新对应专题记录的状态为已抓取
        db.update('update category set status=1 where category_id=%s', category_id)
        logging.info('当前专题[%s]所有文章获取完毕' % category_id)


# 主函数
def main():
    # 从数据库中获取一条未抓取的专题数据
    rs = db.get_one('select * from category where status=0')
    while rs and rs.get('category_id'):
        category_id = rs.get('category_id').decode('utf-8')
        # 从专题数据中获取所有文章ID
        get_all_article(category_id)
        # 尝试获取下一条记录
        rs = db.get_one('select * from category where status=0')
    logging.info('所有文章 ID 获取完毕')
    logging.shutdown()


if __name__ == "__main__":
    # get_article('9ffcda265b39')
    # get_all_article('2f0905cd646b')
    main()
