#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import logging
import time
import pycurl
import chardet
import StringIO


log = logging.getLogger(__name__)


class CurlChecker(object):

    TYPES = [pycurl.PROXYTYPE_HTTP]  # pycurl.PROXYTYPE_SOCKS4, pycurl.PROXYTYPE_SOCKS5]

    def __init__(self, target, timeout):
        self.timeout = timeout
        self.target = target

    def decode(self, raw):
        codepage = chardet.detect(raw)["encoding"]
        log.debug("encoding detected by chardet %s" % codepage)
        return unicode(raw, codepage, "ignore")

    def __call__(self, proxy):
        data = StringIO.StringIO()
        for type_ in self.TYPES:
            try:
                self.curl = pycurl.Curl()
                self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
                self.curl.setopt(pycurl.MAXREDIRS, 3)
                self.curl.setopt(pycurl.CONNECTTIMEOUT, self.timeout)
                self.curl.setopt(pycurl.TIMEOUT, self.timeout)
                self.curl.setopt(pycurl.WRITEFUNCTION, data.write)
                self.curl.setopt(pycurl.PROXY, proxy)
                self.curl.setopt(pycurl.PROXYTYPE, type_)
                self.curl.setopt(pycurl.HTTPGET, 1)
                self.curl.setopt(pycurl.URL, self.target[0])
                t = time.time()
                self.curl.perform()
                delay = time.time() - t
                text = self.decode(data.getvalue())
                text.index(self.target[1])
                return (delay, type_)
            except pycurl.error:
                log.exception('curl proxy test')
            finally:
                self.curl.close()
        raise Exception('%s dead' % proxy)


if __name__ == "__main__":
    check = CurlChecker(["http://opt.com.ua/add/", u"Добавить"], 3)
    print check('173.9.238.104:8080')
    print check('221.2.80.126:8888')
