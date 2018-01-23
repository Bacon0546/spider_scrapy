# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
from urllib import parse
#import urlparse(py2)
from scrapy.loader import ItemLoader

from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from _datetime import datetime

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        """
        1、获取文章列表中的url并交给scrapy下载后交给解析函数进行具体字段的解析
        2、获取下一页的URL并交给scrapy进行下载，下载完成后交给parse
        :param response:
        :return:
        """

        #解析列表页中所有文章的URL并交给scrapy下载后进行解析
        post_nodes =  response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            image_url = parse.urljoin(response.url, image_url)
            post_url = post_node.css("::attr(href)").extract_first("")
            post_url = parse.urljoin(response.url, post_url)
            yield Request(url=post_url, meta={"front_img_url":image_url}, callback=self.parse_detail)

        # 提取下一页交给scrapy进行下载
        next_url =  response.css(".next.page-numbers::attr(href)").extract_first()
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
    def parse_detail(self, response):
        article_item = JobBoleArticleItem()

        #提取文章具体字段
        # 利用xpath
        # title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first("")
        # create_date =  response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()').extract()[0].strip().replace("·", "").strip()
        # praise_num = int(response.xpath('//span[contains(@class, "vote-post-up")]/h10/text()').extract()[0])
        # favor_nums = response.xpath('//span[contains(@class, "bookmark-btn")]/text()').extract()[0]
        # match_re = re.match(".*?(\d+).*", favor_nums)
        # if match_re:
        #     favor_nums = int(match_re.group(1))
        # else:
        #     favor_nums = 0
        # comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]
        # match_re = re.match(".*?(\d+).*", comment_nums)
        # if match_re:
        #     comment_nums = int(match_re.group(1))
        # else:
        #     comment_nums = 0
        #
        # content =  response.xpath("//div[@class='entry']").extract()[0]
        #
        # tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith('评论')]
        # tags = ','.join(tag_list)

        #通过CSS选择器提取字段
        # front_img_url = response.meta.get("front_img_url", "") #文章封面图
        # title = response.css(".entry-header h1::text").extract()[0]
        # create_date = response.css(".entry-meta-hide-on-mobile::text").extract()[0].strip().replace("·", "").strip()
        # praise_num =  int(response.css(".vote-post-up h10::text").extract()[0])
        # favor_nums = response.css(".bookmark-btn::text").extract()[0]
        # match_re = re.match(".*?(\d+).*", favor_nums)
        # if match_re:
        #     favor_nums = int(match_re.group(1))
        # else:
        #     favor_nums = 0
        # comment_nums =  response.css("a[href='#article-comment'] span::text").extract()[0]
        # match_re = re.match(".*?(\d+).*", comment_nums)
        # if match_re:
        #     comment_nums = int(match_re.group(1))
        # else:
        #     comment_nums = 0
        #
        # content = response.css(".entry").extract()[0]
        # tag_list = response.css(".entry-meta-hide-on-mobile a::text").extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith('评论')]
        # tags = ','.join(tag_list)
        #
        # article_item["url_object_id"] = get_md5(response.url)
        # article_item['title'] = title
        # article_item['url'] = response.url
        # try:
        #     create_date = datetime.strptime(create_date, "%Y/%m/%d").date()
        # except Exception as e:
        #     create_date = datetime.now().date()
        # article_item['create_date'] = create_date
        # article_item['front_img_url'] = [front_img_url]
        # article_item['praise_nums'] = praise_num
        # article_item['comment_nums'] = comment_nums
        # article_item['favor_nums'] = favor_nums
        # article_item['tags'] = tags
        # article_item['content'] = content

        #通过item loader 加载item
        front_img_url = response.meta.get("front_img_url", "")  # 文章封面图
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", ".entry-meta-hide-on-mobile::text")
        item_loader.add_value("front_img_url", [front_img_url])
        item_loader.add_css("praise_nums", ".vote-post-up h10::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("favor_nums", ".bookmark-btn::text")
        item_loader.add_css("tags", ".entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        article_item = item_loader.load_item()

        yield article_item #传到pipeline中