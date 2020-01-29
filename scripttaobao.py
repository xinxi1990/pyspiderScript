#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2020-01-28 18:08:45
# Project: testdemo1

"""
爬虫淘宝链接地址
"""
from pyspider.libs.base_handler import *
from six import itervalues
import MySQLdb
import redis


class SQL():
    # 数据库初始化
    def __init__(self):
        # 数据库连接相关信息
        hosts = '192.168.1.103'
        username = 'root'
        password = '123321'
        database = 'pyspider'
        charsets = 'utf8'

        self.connection = False
        try:
            self.conn = MySQLdb.connect(host=hosts, port=8888, user=username, passwd=password, db=database,
                                        charset=charsets)
            self.cursor = self.conn.cursor()
            self.cursor.execute("set names " + charsets)
            self.connection = True
        except Exception as e:
            print("Cannot Connect To Mysql!/n", e)

    def escape(self, string):
        return '%s' % string

    # 插入数据到数据库
    def insert(self, tablename=None, **values):

        if self.connection:
            tablename = self.escape(tablename)
            if values:
                _keys = ",".join(self.escape(k) for k in values)
                _values = ",".join(['%s', ] * len(values))
                sql_query = "insert into %s (%s) values (%s)" % (tablename, _keys, _values)
            else:
                sql_query = "replace into %s default values" % tablename
            try:
                if values:
                    self.cursor.execute(sql_query, list(itervalues(values)))
                else:
                    self.cursor.execute(sql_query)
                self.conn.commit()
                return True
            except Exception as e:
                print("An Error Occured: ", e)
                return False


class Handler(BaseHandler):
    crawl_config = {
    }


    # 每天都要执行
    @every(minutes=24 * 60)
    def on_start(self):
        """
        脚本人口
        :return:
        """
        self.crawl('www.taobao.com', callback=self.index_page)
        # 它将会添加新的任务到采集队列


    # 这个参数是告诉调度器抛弃这个请求，如果这个请求在十天之内爬过
    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        """
        会获得一个所有 Response* 对象. response.doc*是一个pyquery对象
        :param response:
        :return:
        """
        # 正则表达式
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    @config(priority=2)
    def detail_page(self, response):
        """
        标记了detail pages应该先采集
        :param response:
        :return:
        """

        print("######### response url #########" + str(response.url))
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }

    def on_result(self, result):
        """
        去管理采集的结果
        :param result:
        :return:
        """
        print("##################")
        if not result or not result['url']:
            return
        print(result)
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        r.lpush("url", result['url'])
        SQL().insert('t_pyspider_project', **result)


    def on_finished(self):
        pass

    @catch_status_code_error
    def callback(self, response):
        pass