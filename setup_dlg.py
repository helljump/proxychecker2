#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
import settings
import logging


log = logging.getLogger(__name__)


class SetupDialog(QDialog):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        uic.loadUi("assets/setup.ui", self)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        params = settings.STORAGE.get('captcha', {})
        self.antigate_rb.setChecked(params.get('antigate', True))
        self.antigate_le.setText(params.get('antigate_key', ''))
        self.captchabot_rb.setChecked(params.get('captchabot', False))
        self.captchabot_le.setText(params.get('captchabot_key', ''))
        self.ripcaptcha_rb.setChecked(params.get('ripcaptcha', False))
        self.ripcaptcha_le.setText(params.get('ripcaptcha_key', ''))

    def save(self):
        log.debug('save')
        settings.STORAGE['captcha'] = {
            'antigate': self.antigate_rb.isChecked(),
            'antigate_key': self.antigate_le.text(),
            'captchabot': self.captchabot_rb.isChecked(),
            'captchabot_key': self.captchabot_le.text(),
            'ripcaptcha': self.ripcaptcha_rb.isChecked(),
            'ripcaptcha_key': self.ripcaptcha_le.text(),
        }
        self.close()


if __name__ == '__main__':
    w = SetupDialog()
    w.exec_()
