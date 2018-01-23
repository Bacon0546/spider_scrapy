# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import codecs
import json
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi

import MySQLdb
import MySQLdb.cursors


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class MysqlPipeline(object):
    # 同步插入mysql，数据量大时插入速度跟不上
    def __init__(self):
        self.conn = MySQLdb.connect(
            host = 'localhost',
            port = 3306,
            user = 'bacon',
            passwd = '123456',
            db = 'article_spider',
            charset="utf8",
            use_unicode=True
        )
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
        insert into jobbole_article
        # (title, create_date, url, url_object_id, front_img_url, front_img_path, comment_nums, favor_nums, praise_nums, tags, content)
        (title, create_date, url, url_object_id, front_img_url, comment_nums, favor_nums, praise_nums, tags, content)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(
            insert_sql,
            (
                item['title'],
                item['create_date'],
                item['url'],
                item['url_object_id'],
                item['front_img_url'],
                # item['front_img_path'],
                item['comment_nums'],
                item['favor_nums'],
                item['praise_nums'],
                item['tags'],
                item['content']
            )
        )
        self.conn.commit() #同步插入数据

class MysqlTwistedPipeline(object):
    #采用twisted异步插入mysql
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparmas = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWD"],
            charset = "utf8",
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparmas)

        return cls(dbpool)
    def process_item(self, item, spider):
        #使用twisted将mysql插入变为异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error) #处理异常

    def handle_error(self, failure):
        #处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        #执行具体的插入

        insert_sql = """
        insert into jobbole_article
        # (title, create_date, url, url_object_id, front_img_url, front_img_path, comment_nums, favor_nums, praise_nums, tags, content)
        (title, create_date, url, url_object_id, front_img_url, comment_nums, favor_nums, praise_nums, tags, content)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        
        """
        cursor.execute(
            insert_sql,
            (
                item['title'],
                item['create_date'],
                item['url'],
                item['url_object_id'],
                item['front_img_url'],
                # item['front_img_path'],
                item['comment_nums'],
                item['favor_nums'],
                item['praise_nums'],
                item['tags'],
                item['content']
            )
        )

class JsonWithEncodingPipeline(object):
    #自定义json文件的导出
    def __init__(self):
        self.file = codecs.open("article.json", "w", encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item
    def spider_closed(self, spider):
        self.file.close()

class JsonExporterPipeline(object):
    #调用scrapy提供的惊悚 exporter导出json文件
    def __init__(self):
        self.file = open('article_exporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()
    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_img_url" in item:
            for ok, value in results:
                img_file_path = value['path']
            item["front_img_path"] = img_file_path

        return item