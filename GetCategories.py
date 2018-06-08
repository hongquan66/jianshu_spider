#!/usr/bin/env python
# encoding: utf-8

"""
@file: GetCategories.py Build By Python 3.6.5
@time: 2018/5/10 17:48
@desc: 收集简书的专题数据
@author: hongquanpro@126.com
"""
import datetime
import requests
import re
import time

from jianshu.util.Mysql import Mysql

headers = {
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept - Language': 'zh - CN, zh;q = 0.8',
    'Connection': 'close',
    'Cookie': 'UM_distinctid=15b89d53a930-02ab95f11ccae2-51462d15-1aeaa0-15b89d53a9489b; CNZZDATA1258679142=1544557204-1492664886-%7C1493280769; remember_user_token=W1szNDgxMjU3XSwiJDJhJDEwJDlSS3VLcFFWMlZzNFJuOFFNS1JQR3UiLCIxNDk0MjEzNDQ3LjYwODEwNzgiXQ%3D%3D--9241542a4e44d55acaf8736a1d57dd0e96ad4e7a; _ga=GA1.2.2016948485.1492666105; _gid=GA1.2.824702661.1494486429; _gat=1; Hm_lvt_0c0e9d9b1e7d617b3e6842e85b9fb068=1494213432,1494213612,1494321303,1494387194; Hm_lpvt_0c0e9d9b1e7d617b3e6842e85b9fb068=1494486429; _session_id=czl6dzVOeXdYaEplRVdndGxWWHQzdVBGTll6TVg5ZXFDTTI5cmN2RUsvS2Y2d3l6YlkrazZkZWdVcmZDSjFuM2tpMHpFVHRTcnRUVnAyeXhRSnU5UEdhaGMrNGgyMTRkeEJYOE9ydmZ4N1prN1NyekFibkQ5K0VrT3paUWE1bnlOdzJrRHRrM0Z2N3d3d3hCcFRhTWdWU0lLVGpWWjNRdjArZkx1V2J0bGJHRjZ1RVBvV25TYnBQZmhiYzNzOXE3VWNBc25YSS93WUdsTEJFSHVIck4wbVI5aWJrUXFaMkJYdW41WktJUDl6OVNqZ2k0NWpGL2dhSWx0S2FpNzhHcFZvNGdQY012QlducWgxNVhoUEN0dUpCeUI4bEd3OXhiMEE2WEplRmtaYlR6VTdlZXFsaFFZMU56M2xXcWwwbmlZeWhVb0dXKzhxdEtJaFZKaUxoZVpUZEZPSnBGWmF3anFJaFZpTU9Icm4wcllqUFhWSzFpYWF4bTZmSEZ1QXdwRWs3SHNEYmNZelA4VG5zK0wvR0MwZDdodlhZakZ6OWRVbUFmaE5JMTIwOD0tLXVyVEVSeVdOLy9Cak9nVG0zV0hueVE9PQ%3D%3D--ea401e8c501e7b749d593e1627dbaa88ab4befc2',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36',
    'Host': 'www.jianshu.com',
    "X-Requested-With": 'XMLHttpRequest'
}

# 数据库管理类
db = Mysql()

# 专题列表
order_by = ['recommend', 'hot', 'city', 'schoolyard']
page_num = 1
url = 'https://www.jianshu.com/recommendations/collections?order_by=%s&page=%d' % (order_by[1], page_num)
categories = []


# 获取所有专题数据
def get_all_categories():
    global url, page_num
    categories_html = requests.get(url, headers=headers).text
    matches = re.findall(r'href="/c/(.*?)"', categories_html, re.S)
    for match in matches:
        if match not in categories:
            categories.append(match)
    # 判断是否有下一页
    if 'load-more-btn display_false' not in categories_html:
        page_num += 1
        url = 'https://www.jianshu.com/recommendations/collections?order_by=%s&page=%d' % (order_by[1], page_num)
        print('准备爬取第 %d 页: %s' % (page_num, url))
        get_all_categories()
    else:
        print('获取专题数据 %d 条，更新于 %s\n' % (len(categories), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    return


# 获取专题数据详情
def get_category(category_id):
    category_info_url = 'https://www.jianshu.com/c/%s' % category_id
    category_html = requests.get(category_info_url, headers=headers).text
    # 获取专题标题
    category_title = re.findall(r'<div class="title">.*<a class="name.*?>(.*?)</a>.*</div>', category_html, re.S)
    if len(category_title) > 0:
        category_title = category_title[0]
    else:
        category_title = "error"
    # 获取文章和粉丝人数  (-\d*|\d*) 是因为有数据返回负数
    category_data = re.findall(r'收录了(-\d*|\d*)篇文章 · (-\d*|\d*)人关注', category_html, re.S)
    article_count = category_data[0][0]
    fans = category_data[0][1]

    # print('添加数据成功. [%s]《%s》 文章：%s 粉丝：%s' % (category_id, category_title.encode('utf-8'), article_count, fans))

    # 保存到数据库
    result = db.insert_one('insert into category(category_id, title, article_count, fans, created, status) '
                           'values(%s, %s, %s, %s, %s, 0)',
                           (category_id, category_title, article_count, fans,
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    if result > 0:
        print('添加数据成功. [%s]《%s》 文章：%s 粉丝：%s' % (category_id, category_title.encode('utf-8'), article_count, fans))
    else:
        print('保存专题数据失败! ID = %s' % category_id)
    return


if __name__ == "__main__":
    # 获取热门专题列表
    get_all_categories()
    print('***************** 专题信息 ***************** ')
    for cid in categories:
        get_category(cid)
