#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import logging
import time
import random
import settings
from grab import Grab, error
import captcha


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

#, threads %i', threading.active_count()


def get_antigate():
    ag = captcha.BaseCaptcha()
    params = settings.STORAGE.get('captcha', {})
    for k, v in params.items():
        if v:
            if k == 'antigate' and params['antigate_key']:
                ag = captcha.Antigate(params['antigate_key'])
            elif k == 'captchabot' and params['captchabot_key']:
                ag = captcha.CaptchaBot(params['captchabot_key'])
            elif k == 'ripcaptcha' and params['ripcaptcha_key']:
                ag = captcha.RipCaptcha(params['ripcaptcha_key'])
    return ag


def googlecom(q, baseurl="http://www.google.com"):
    g = Grab(headers=random.choice(settings.CONFIG['headers']))
    #if __name__ == '__main__':
    #    g.setup(log_dir='dumps')
    g.go(baseurl)
    g.set_input('q', q)
    g.submit()
    while True:
        links = g.doc.select('//h3[@class="r"]/a/@href')
        if not links:
            log.debug('no links on page')
            return
        for link in links:
            yield link.text()
        try:
            nexturl = g.doc.select('//a[@id="pnnext"]/@href').text()
        except error.DataNotFound:
            log.debug('no next button')
            return
        g.go(nexturl)
        time.sleep(1)


def googleru(q):
    return googlecom(q, "http://www.google.ru")


def yandex(q):
    ag = get_antigate()
    g = Grab(headers=random.choice(settings.CONFIG['headers']))
    g.go('http://ya.ru')
    g.set_input('text', q)
    #g.go('http://yandex.ru/yandsearch?text=free+proxy+list&lr=9')
    g.submit()
    while True:
        try:
            capurl = g.doc.select('//img[starts-with(@src,"http://yandex.ru/captchaimg")]/@src')
            url = capurl.text()
            g2 = g.clone()
            data = g2.go(url)
            rep = ag.get_text(data.body_as_bytes(), 'captcha.gif', is_russian=1)
            g.set_input('rep', rep)
            g.submit()
        except error.DataNotFound:
            pass  # it's ok
        links = g.doc.select('//a[contains(@class,"serp-item__title-link")]/@href')
        if not links:
            log.debug('no links on page')
            return
        for link in links:
            yield link.text()
        try:
            nexturl = g.doc.select('//a[contains(@class,"pager__button_kind_next")]/@href').text()
        except error.DataNotFound:
            log.debug('no next button')
            return
        g.go(nexturl)
        time.sleep(1)
        

ENGINES = (
    ['yandex', True, yandex],
    ['google.com', True, googlecom],
    ['google.ru', True, googleru]
)


if __name__ == "__main__":
    for l in yandex("free proxy list"):
        print l

