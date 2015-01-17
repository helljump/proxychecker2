#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import settings
import logging
import requests
from lxml import html
import sys
import os
import random
import time


log = logging.getLogger(__name__)


def _dump(rc, *args, **kwargs):
    dname = os.path.expanduser('dump.html')
    fout = open(dname, 'wb')
    fout.write(rc.content)
    fout.close()


def _make_session():
    sess = requests.session()
    if not hasattr(sys, "frozen"):
        sess.hooks = dict(response=_dump)
    sess.headers = random.choice(settings.CONFIG['headers'])
    return sess


def yandex(q):
    sess = _make_session()
    rc = sess.get('http://yandex.ru')
    time.sleep(1)
    page = 0
    while True:
        params = {'text': q, 'lr': 9}
        if page > 0:
            params['p'] = page
        rc = sess.get('http://yandex.ru/yandsearch', params=params)
        soup = html.fromstring(rc.content)
        links = soup.xpath('//a[@class="b-serp-item__title-link"]/@href')
        for link in links:
            yield link
        page += 1
        time.sleep(1)


def googlecom(q, baseurl="http://www.google.com/search"):
    sess = _make_session()
    start = 0
    links_on_page = 10

    while True:
        params = {"q": q, "num": links_on_page}
        if start > 0:
            params["start"] = start
        rc = sess.get(baseurl, params=params)
        soup = html.fromstring(rc.content)
        links = soup.xpath('//h3[@class="r"]/a/@href')
        for link in links:
            yield link
        start += links_on_page
        time.sleep(1)


def googleru(q):
    return googlecom(q, "http://www.google.ru/search")


ENGINES = (
    ['yandex', True, yandex],
    ['google.com', True, googlecom],
    ['google.ru', True, googleru]
)

if __name__ == "__main__":
    c = 100
    s = set()
    for link in yandex(u"free proxy list"):
        print link
        s.add(link)
        c -= 1
        if not c:
            break
    print len(s)
