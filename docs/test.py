# -*- coding: utf-8 -*-


from PyQt4 import QtCore, QtGui


class ModalWind(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ModalWind, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle(u"Модальное окно")
        self.resize(200, 50)
        butt_hide = QtGui.QPushButton(u'Закрыть модальное окно')
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(butt_hide)
        self.setLayout(vbox)
        butt_hide.clicked.connect(self.close)

    def hideEvent(self, event):
        self.parent().hide()


class MainWind(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MainWind, self).__init__(parent)
        self.setWindowTitle(u"Главное окно")
        self.resize(200, 100)
        butt_show = QtGui.QPushButton(u'Показать модальное окно')
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(butt_show)
        self.setLayout(vbox)
        butt_show.clicked.connect(self.on_show)

    def on_show(self):
        win = ModalWind(self)
        win.setParent(self)
        win.show()


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    window = MainWind()
    window.show()
    mw = ModalWind(window)
    mw.show()
    sys.exit(app.exec_())
