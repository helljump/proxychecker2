#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#@author: snoa

import bcryptor
from PyQt4 import QtGui


class Dialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.resize(559, 241)
        gridLayout = QtGui.QGridLayout(self)
        self.lineEdit = QtGui.QLineEdit(self)
        self.lineEdit.returnPressed.connect(self.calc)
        gridLayout.addWidget(self.lineEdit, 0, 0, 1, 1)
        self.textEdit = QtGui.QTextEdit(self)
        gridLayout.addWidget(self.textEdit, 1, 0, 1, 1)

    def calc(self):
        egg = unicode(self.lineEdit.text())
        hasher = bcryptor.Bcrypt()
        obj = hasher.create(egg)
        self.textEdit.setText(obj.encode("base64"))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Dialog().exec_()
