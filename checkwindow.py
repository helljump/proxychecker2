#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"

import logging

log = logging.getLogger(__name__)

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic


log = logging.getLogger(__name__)


class CheckWindow(QMainWindow):

    canceled = pyqtSignal()

    def __init__(self, title, label, ctext, from_=0, to=0, parent=None):
        QMainWindow.__init__(self, parent)
        uic.loadUi("assets/progress.ui", self)
        self.setWindowTitle(title)
        self.label.setText(label)
        self.progressBar.setRange(from_, to)

    def closeEvent(self, event):
        self.canceled.emit()
        event.accept()

    def cancel(self):
        self.close()

    def setText(self, text):
        self.label.setText(text)

    def incValue(self, v=1):
        self.setValue(self.value() + v)

    def setValue(self, v):
        self.progressBar.setValue(v)

    def value(self):
        return self.progressBar.value()
