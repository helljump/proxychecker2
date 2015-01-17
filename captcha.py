#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"

import logging
import requests
import time
import mimetypes


log = logging.getLogger(__name__)


class AntigateError(Exception):
    pass


class BaseCaptcha(object):

    TIMEOUT = 60
    SLEEPTIME = 5

    def get_balance(self):
        return -1

    def get_text(self, *args, **kwargs):
        return ''


class Antigate(BaseCaptcha):
    """
    >>> ag = Antigate('*****9404cccf08797ec7d76bbe5224f')
    >>> float(ag.get_balance()) > -1
    True
    >>> egg = ag.get_text(open('/work/cm2/test/captcha.png', 'rb').read())
    >>> print egg.lower()
    nxkm
    """

    SOFT_ID = '48'
    URL = "http://antigate.com"

    def __init__(self, key):
        self.sess = requests.Session()
        self.key = key

    def check_error(self, rc):
        if rc.text.startswith("ERROR_"):
            raise AntigateError(rc.text)

    def get_balance(self):
        params = {
            'key': self.key,
            'action': 'getbalance'
        }
        rc = self.sess.get(self.URL + '/res.php', params=params)
        self.check_error(rc)
        return rc.text

    def _send(self, data, fname, **kwargs):
        t, e = mimetypes.guess_type(fname)
        files = {
            'file': (fname, data, t)
        }
        params = {
            'key': self.key,
            'soft_id': self.SOFT_ID,
            'method': 'post'
        }
        params.update(kwargs)
        rc = self.sess.post(self.URL + "/in.php", data=params, files=files)
        #rc = self.sess.post(self.URL + "/post", data=params, files=files)
        #import codecs
        #codecs.open('dump.txt', 'w', 'utf8').write(rc.text)
        self.check_error(rc)
        try:
            cap_id = rc.text.split("|")[1]
        except IndexError:
            log.exception(rc.text)
        return cap_id

    def _recv(self, cap_id):
        params = {
            'key': self.key,
            'soft_id': self.SOFT_ID,
            'action': 'get',
            'id': cap_id
        }
        rc = self.sess.get(self.URL + "/res.php", params=params)
        self.check_error(rc)
        if rc.text == "CAPCHA_NOT_READY":
            return None
        log.debug('rc %s', rc.text)
        text = rc.text.split("|")[-1]
        return text

    def get_text(self, data, fname="captcha.png", **kwargs):
        cap_id = self._send(data, fname, **kwargs)
        log.debug("cap_id %s", cap_id)
        t = time.time()
        while time.time() - t < self.TIMEOUT:
            answer = self._recv(cap_id)
            if answer:
                log.debug("captcha_text %s", answer)
                return answer
            log.debug("catcha is not ready, sleep %i seconds", self.SLEEPTIME)
            time.sleep(self.SLEEPTIME)
        else:
            raise AntigateError("ERROR_ANTIGATE_TIMEOUT")


class CaptchaBot(Antigate):
    """ captchabot with antigate interface

    >>> ag = CaptchaBot('*****504750060896ad6f13b5d3e7a9e')
    >>> float(ag.get_balance()) > -1
    True
    >>> egg = ag.get_text(open('/work/cm2/test/captcha.png', 'rb').read())
    >>> print egg.lower()
    nxkm
    """

    SOFT_ID = '174015'
    URL = 'http://captchabot.com'


class RipCaptcha(Antigate):
    """ ripcaptcha with antigate interface

    >>> ag = RipCaptcha('*****1b3be91baab890f9154b227c569')
    >>> float(ag.get_balance()) > -1
    True
    >>> egg = ag.get_text(open('/work/cm2/test/captcha.png', 'rb').read())
    >>> print egg.lower()
    nxkm
    """

    SOFT_ID = '1315'
    URL = 'http://ripcaptcha.com'


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    import doctest
    doctest.testmod()
