#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


#TODO: регексп с очисткой тегов


import settings
import logging
import requests
import sys
import os
import random
import re
import socket


log = logging.getLogger(__name__)


def _dump(rc, *args, **kwargs):
    dname = os.path.expanduser('dump.html')
    if os.path.isfile(dname) and not os.access(dname, os.W_OK):
        return
    log.info('dump')
    fout = open(dname, 'wb')
    egg = getattr(rc, 'content', rc)
    fout.write(egg)
    fout.close()


def _make_session(timeout=30, dump=True):
    socket.setdefaulttimeout(timeout)
    sess = requests.session()
    sess.timeout = timeout
    if not hasattr(sys, "frozen") and dump:
        sess.hooks = dict(response=_dump)
    sess.headers = random.choice(settings.CONFIG['headers'])
    return sess


def parse(link):
    ipaddr = re.compile("((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[\w\-]{2,20}\.\w{2,4})\:(\d{2,6}))")
    #tags = re.compile(r'<(?!(?:a\s|/a|!))[^>]*>')
    sess = _make_session()
    rc = sess.get(link)
    #egg = tags.sub('', rc.content)
    #soup = html.fromstring(rc.content)
    #egg = html.tostring(soup, method='text', encoding='utf-8')
    #_dump(egg)
    for item in ipaddr.finditer(rc.content):
        address = item.groups(0)[0]
        yield address

if __name__ == "__main__":
    for link in parse('http://spys.ru/'):
    #for link in parse('http://hidemyass.com/proxy-list/'):
        print link
