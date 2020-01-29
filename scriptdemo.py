import sys

reload(sys)
sys.setdefaultencoding('utf8')
import copy
import json
import time, datetime
import re
from pyspider.libs.base_handler import *
from pyquery import PyQuery as pq

result_template = {
    "info_id": "",  # 资讯信息编号（自增）
    "url": "",  # 原文URL
    "title": "",  # 标题
    "subheading": "",  # 副标题
    "fetch_time": "",
    "pub_time": "",  # 发布时间 文章内容中的发布时间，并非爬虫爬去到文章的时间
    "sort": "",  # 分类接口 ？
    "summary": "",  # 资讯信息摘要
    "content": "",  # 正文
    "persons": "",  # 涉及到的人
    "companys": "",  # 涉及到的公司
    "stocknames": "",  # 涉及到的股票
    "stockcodes": "",  # 涉及到的股票代码
    "industries": "",  # 涉及的行业
    "sections": "",  # 涉及的板块
    "others": "",
    "info_type": "",  # 文章所属类型  公告 / 新闻
    "source": "",  # 发布单位
    "info_channel": "",  # 2级标题/频道及以下所有标题/频道。不同频道之间，使用下划线"_"连接，不包含"首页"及"正文"。
    "editor": "",  # 编辑者
    "keywords": "",  # 文章自带关键词
    "datetime": "",  # 文章采集时间
    "imageAttachment": "null",  # 图片附件
    "fileAttachment": "null",  # 文件附件

    "html": "",
}

source_name = "中国金融网"
source_list = [
    {
        "url": "http://www.cnfinance.cn/articles/?template=sample_397.html&page=%s",
        "source_channel": "新闻",
    },
    {
        "url": "http://www.financeun.com/articleList/1.shtml?page=%s",
        "source_channel": "焦点", "source_name": "中国金融网"
    }
]

# headers=headers,

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
}


class Handler(BaseHandler):
    crawl_config = {
    }

    @every(minutes=2 * 60)
    def on_start(self):
        for source in source_list:
            url = source['url']
            source_channel = source['source_channel']

            for i in range(1, 2):
                self.crawl(url % str(i), headers=headers, callback=self.index_page, save=source)

    @config(age=1)
    def index_page(self, response):
        for each in response.doc('dl.dl_artListB dt a').items():
            href = each.attr.href
            if href:
                self.crawl(href, headers=headers, callback=self.detail_page, save=response.save)

    @config(priority=2, age=10 * 24 * 60 * 60)
    def detail_page(self, response):
        result = copy.deepcopy(result_template)
        result["url"] = response.url
        result["source_channel"] = response.save['source_channel']
        result["source_name"] = source_name

        if response.doc('div.contDetailsBox').html():
            result["html"] = response.doc('div.contDetailsBox').html().strip()
            result["editor"] = response.doc('p.p_author.span').text().replace('作者：', '')
            result["source"] = response.doc(' p.p_artInfo span ').eq(1).text().replace('摘自：', '')
            result["title"] = response.doc('h2.h2_artDetails').text()

            result["pub_time"] = response.doc('p.p_artInfo span ').eq(0).text().replace(u'年', '-').replace(u'月',
                                                                                                           '-').replace(
                u'日', '')

        result["content"] = get_content_from_html(result["html"])
        result["pub_time"] = str_2_timestamp(result["pub_time"])
        result["pub_time"] = get_pub_time(result["pub_time"])
        result["datetime"] = get_now_time()
        self.send_message(self.project_name, result, url=result["url"])

    def json_handler(self, response):
        result = copy.deepcopy(result_template)
        data = json.loads(response.text)
        result["title"] = response.save['title']
        result["author"] = response.save['author']
        html = "<h1>%s</h1>" % response.save['title']
        html += data['data']['content']
        result['html'] = html
        result["content"] = get_content_from_html(html)
        result["summary"] = data['data']['content_short']
        result['pub_time'] = timestamp_to_str(response.save['display_time'])
        self.send_message(self.project_name, result, url=result["url"])

    def on_message(self, project, msg):
        return msg


def get_content(response):
    import chardet
    from readability import Document
    import html2text
    char_encoding = chardet.detect(response.content)  # bytes
    # print(char_encoding)
    if char_encoding["encoding"] == "utf-8" or char_encoding["encoding"] == "utf8":
        doc = Document(response.content.decode("utf-8"))
    else:
        doc = Document(response.content.decode("gbk", "ignore"))
    title = doc.title()
    content = doc.summary()
    h = html2text.HTML2Text()
    h.ignore_links = True
    # h.ignore_images = True
    d_data = h.handle(content).replace("-\n", "-")
    return d_data.rstrip()


def str_2_timestamp(time_str, fmt="%Y-%m-%d %H:%M:%S"):
    if not time_str:
        return ""
    elif len(time_str) == 9:
        fmt = "%Y-%m-%d"
    elif len(time_str) == 10:
        fmt = "%Y-%m-%d"
    elif len(time_str) == 13:
        fmt = "%Y-%m-%d %H"
    elif len(time_str) == 16:
        fmt = "%Y-%m-%d %H:%M"
    return int(time.mktime(time.strptime(time_str, fmt)))


def get_content_from_html(html):
    import html2text
    h = html2text.HTML2Text()
    h.ignore_links = True
    # h.ignore_images = True
    d_data = h.handle(html).replace("-\n", "-")
    return d_data.rstrip()


def get_pub_time(response):
    # date_time = response.doc('div.content div.titleHead div.newsDate').text()
    # date_time = response.doc("div#article.article span#pubtime_baidu").text()

    # return date_time

    # timeArray = time.strptime(response, "%Y-%m-%d %H:%M:%S")
    # 转换成时间戳
    # timestamp = time.mktime(timeArray)
    return str(response * 10)[0:10]


def re_search_time(time_str):
    r_str = r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2}|\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}|\d{4}-\d{1,2}-\d{1,2})"
    mat = re.search(r_str, time_str)
    if not mat:
        return ""
    return mat.group(0)


def re_sub_html(html):
    return re.sub(r'<!--.*?-->', '', html)


def get_now_time():
    return str(int(time.time()))

