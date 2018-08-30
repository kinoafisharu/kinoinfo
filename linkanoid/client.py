# -*- coding: utf-8 -*-
import os
import re
import urllib
import logging
import requests
import requests_cache
from urlparse import urlparse
import hashlib

VERSION = "0.0.2"
logging_level = logging.ERROR

logging.basicConfig(level=logging_level)


class Client():
    """
    TrustlinkClient - Python links inserter from trustlink.ru.
    """

    def __init__(self, *args, **kwargs):
        self.remote_addr = os.environ.get("REMOTE_ADDR", "0.0.0.0")
        self.TRUSTLINK_USER = os.environ.get("TRUSTLINK_USER", "")
        self.cache_reloadtime = 3600                    # берём данные из кеша если он свежее этого времени
        self.charset = "DEFAULT"                        # кодировка, в которой запрашиваем данные от трастлинка
        self.force_show_code = False                    # обрамляем вывод кодом взятым от трастлинка
        self.host = os.environ.get("HTTP_HOST", "")     # наш хост
        self.is_static = False                          # если да, то будет неизменяемый request_uri
        self.is_robot = False                           # робот ли мы?
        self.multi_site = False
        self.request_uri = ""
        self.server = "http://db.trustlink.ru"          # сервер трастлинка, откуда забираем данные
        self.socket_timeout = 6
        self.template = "template"                      # имя шаблона к которому будет добавлен cуффикс .tpl.html
        self.test = False
        self.test_count = 4                             # количество ссылок на страницу если мы в режиме тестирования
        self.tpath = os.path.normpath(os.path.dirname(__file__))  # путь, где находится шаблон
        self.cache_path = '%s/tmp' % os.path.normpath(os.path.dirname(__file__))
        self.size = None
        self.use_ssl = False
        self.verbose = True
        self.links_delimiter = None
        self.links_page = []
        self.links = {}
        self.links_count = None
        self._links_loaded = False

        if args:
            self.host = args[0]
        elif kwargs:
            for key, value in kwargs.items():
                vars(self)[key] = value

        if not self.TRUSTLINK_USER:
            raise ValueError("TRUSTLINK_USER is not set.")

        self.host = re.sub(r'(?i)^www\.', '', self.host)  # избавляемся от "www." в имени домена

        if not self.request_uri:
            self.request_uri = os.environ.get("REQUEST_URI", "/")
            if self.is_static:
                self.request_uri = re.sub(r'\?.*$', '', self.request_uri)  # удаляем QUERY_STRING
                self.request_uri = re.sub(r'//*', '/', self.request_uri)   # удаляем дублирующиеся слеши

        self.request_uri = urllib.unquote(self.request_uri)

        if os.environ.get("HTTP_TRUSTLINK") == self.TRUSTLINK_USER:
            self.test = True
            self.is_robot = True
            self.verbose = True

    def load_links(self):
        """
        Загрузка контента с trustlink
        """
        
        requests_cache.install_cache(
            self.cache_path + '/trustlink-links-python_cache.sql',
            backend='sqlite',
            expire_after=self.cache_reloadtime
        )
        
        url = "/".join([self.server, self.TRUSTLINK_USER, self.host.lower(), self.charset.upper() + ".text"])
        data = requests.get(url)  # Выполняем запрос к trustlink
        data.encoding = self.charset  # Устанавливаем форсированно указанную кодировку
        content = data.text

        if re.match(re.compile('^FATAL ERROR:'), content):
            raise ValueError("Fatal error")

        self.file_size = len(content)
        self.links = self.__parse_links(content)  # разбираем контент и складываем в self.links

        if self.links.get("__trustlink_debug__"): # если трастлинк отдал особые данные, то переключаем режимы (не уверен, что это хорошо, позволять трастлинку управлять нашим приложением)
            self.verbose = self.force_show_code = True
        if self.links.get("__trustlink_delimiter__"):
            self.links_delimiter = self.links["__trustlink_delimiter__"]

        if self.test: # в режиме тестирования заполняем страничку размноженной тестовой ссылкой
            if type(self.links["__test_tl_link__"]) == dict:
                self.links_page = [self.links["__test_tl_link__"]] * self.test_count
        else: # а в боевом режиме в страничку заносим ссылки относящиеся к нашему request_uri
            if self.links.get(self.request_uri):
                self.links_page = self.links[self.request_uri]
        
        self.links_count = len(self.links_page)
        self._links_loaded = True

    def __parse_links(self, content):
        """
        Разбор контента,
        пришедшего от trustlink
        """

        links = {}

        test_tl_link_regexp = re.compile(r'(?ism)__test_tl_link__:(.*?)(\n\n)')
        test_tl_link = re.findall(test_tl_link_regexp, content)  # ищем тестовую сылку

        if test_tl_link:
            links["__test_tl_link__"] = {}
            for line in test_tl_link[0][0].split("\n"):
                links["__test_tl_link__"][line.split(":")[0]] = ":".join(line.split(":")[1:])

        content = re.sub(test_tl_link_regexp, "", content)  # чистим контент от тестовых ссылок, чтоб они нам не попадались при поиске служебных слов

        match = dict(re.findall(r'__([a-z_]+)__:(.*)\n', content))  # ищем служебные теги, заносим их в хэш
        match["trustlink_robots"] = match["trustlink_robots"].split(" <break> ")  # преобразовываем строку с ip-шниками роботов в массив

        for key, value in match.items(): # сохраняем все служебные данные в нужном формате
            links["__%s__" % key] = value

        links[self.request_uri] = []
        cur_links_txt = re.findall('(?ism)%s?:(.*?)(\n\n)' % self.request_uri, content)
        if cur_links_txt:
            for cur_link in cur_links_txt[0][0].split(" <break> "):
                tmp_links = {}
                for line in cur_link.split("\n"):
                    if not line:
                        continue
                    tmp_links[line.split(":")[0]] = ":".join(line.split(":")[1:])
                links[self.request_uri].append(tmp_links)

        return links

    def build_links(self):
        if not self._links_loaded:
            self.load_links()
        
        result = ''  # здесь будет результат

        # если от трастлика пришел спецкод и (у нас включен особый режим или нас запросил трастлинковский робот), то вставляем этот спецкод
        if self.links["__trustlink_start__"] \
            and self.force_show_code \
            or self.remote_addr in self.links["__trustlink_robots__"]:
            result += self.links["__trustlink_start__"]
        
        # если многословный режим или нас запросил трастлинковский робот, то ...
        if self.verbose or self.remote_addr in self.links["__trustlink_robots__"]:
            result += """<!-- REQUEST_URI={request_uri_env} -->

<!--
L {version}
REMOTE_ADDR={remote_addr}
request_uri={request_uri}
charset={charset}
is_static={is_static}
multi_site={multi_site}
file_size={file_size}
lc_links_count={lc_links_count}
left_links_count={left_links_count}
-->""".format(request_uri_env=os.environ.get("REQUEST_URI", ""),
                version=VERSION,
                remote_addr=self.remote_addr,
                request_uri=self.request_uri,
                charset=self.charset,
                is_static=self.is_static,
                multi_site=self.multi_site,
                file_size=self.file_size,
                lc_links_count=self.links_count,
                left_links_count=self.links_count)
        
        tpl_filename = self.tpath + "/" + self.template + ".tpl.html"  # имя файла с шаблоном
        
        try:
            tpl = open(tpl_filename, "r").read()  # заглатыавем содержимое файла в переменную
        except IOError:
            raise IOError("Template file no found")

        if not re.search(r"(?is)<\{block\}>(.*)<\{\/block\}>", tpl):
            raise StandardError("Wrong template format: no <{block}><{/block}> tags")

        blockT = tpl.split('<{block}>')[1].split('<{/block}>')[0]  # здесь тело блока без обрамляющих тегов
        
        # проверяем наличие шаблона на присутсвие необходимых тегов
        for tag in ["head_block", "/head_block", "link", "text", "host"]:
            if not "<{%s}>" % tag in blockT:
                raise StandardError("Wrong template format: no <{%s}> tag." % tag)

        text = ''  # сюда будем добавлять готовые прошаблонизированные ссылочки

        for link in self.links_page:  # это ссылки для нашей страницы

            if type(link) != dict:
                raise StandardError("link is not a hashref: $link")

            if not link["url"] or not link["text"]: #  or not link["anchor"]
                raise StandardError("format of link must be a hash('anchor'=>\$anchor,'url'=>\$url,'text'=>\$text)")

            host = urlparse(link["url"]).netloc

            if not host:
                raise StandardError("wrong format of url: %s" % link["url"])

            if not "." in host:
                raise StandardError("wrong host: %s in url %s" % (host, link["url"]))

            host = re.sub(r'(?i)^www\.', '', host)

            a = blockT
            a = re.sub(r"(?i)<\{text\}>", link["text"], a)
            a = re.sub(r"(?i)<\{host\}>", host, a)

            if link.get("anchor"):
                href = link.get("punicode_url", link.get("url"))
                a = re.sub(r"(?i)<\{link\}>", "<a href='%s'>%s</a>" % (href, link["anchor"]), a)
                a = re.sub(r"(?i)<\{head_block\}>", "", a)
                a = re.sub(r"(?i)<\{\/head_block\}>", "", a)
            else:
                a = re.sub(r"(?is)<\{head_block\}>(.*)<\{\/head_block\}>", "", a)

            text += a

        tpl = re.sub(r"(?ism)<\{block\}>(.*)<\{\/block\}>", text, tpl)  # заменяем блок сформированным текстом
        result += tpl  # и добавляем его в результат

        # если от трастлика пришел спецкод и (у нас включен особый режим или нас запросил трастлинковский робот), то вставляем этот спецкод
        if self.links.get("__trustlink_end__") \
            and self.force_show_code \
            or self.request_uri in self.links["__trustlink_robots__"]:
            result += self.links["__trustlink_end__"]

        # для тестового режима, если это не режим робота обрамляем в noindex
        if self.test and not self.is_robot:
            result = '<noindex>' + result + '</noindex>'

        result = result + self.uptolike_tag()

        return result

    def uptolike_tag(self):
      uptolike_hash = 'tl' + hashlib.sha1(self.host).hexdigest()

      result = '<script async="async" src="https://w.uptolike.com/widgets/v1/zp.js?pid=' + uptolike_hash + '" type="text/javascript"></script>'

      return result
