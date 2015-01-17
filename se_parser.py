#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
import searchengines
import settings
import logging
import itertools


log = logging.getLogger(__name__)


class ParseThread(QThread):

    process = pyqtSignal(QString)
    fail = pyqtSignal(QString)
    done = pyqtSignal()

    def __init__(self, sources, qty, parent):
        super(ParseThread, self).__init__(parent)
        self.sources = sources
        self.qty = qty
        self.active = True

    def get_text(self, err):
        message = 'unknown'
        try:
            message = unicode(err)
            log.debug('exception in unicode')
        except UnicodeDecodeError:
            message = str(err).decode('cp1251', 'replace')
            log.debug('exception in str')
        except Exception:
            log.exception("unknown in thread")
        return message

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        try:
            for se in itertools.cycle(self.sources):
                log.debug('process: %s', se)
                link = se.next()
                self.process.emit(link)
                self.qty -= 1
                if not self.active or not self.qty:
                    break
            self.done.emit()
        except Exception, err:
            log.exception("catched in thread")
            self.fail.emit(self.get_text(err))
        log.debug("stop %s" % QThread.currentThread())

    def die(self):
        self.active = False
        #self.wait(100)
        #self.terminate()
        log.debug("die %s" % QThread.currentThread())


class MyProgressDialog(QProgressDialog):
    def __init__(self, title, label, cancel, from_=0, to_=0, parent=None):
        QProgressDialog.__init__(self, label, cancel, from_, to_, parent)
        self.setWindowTitle(title)
        self.setModal(True)

    def setText(self, text):
        self.setLabelText(text)

    def incValue(self, v=1):
        self.setValue(self.value() + v)


class SEModel(QAbstractListModel):
    def __init__(self, data):
        QAbstractListModel.__init__(self)
        self._data = data

    def rowCount(self, index):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole:
            row = index.row()
            value = self._data[row][0]
            return QVariant(value)
        elif role == Qt.CheckStateRole:
            row = index.row()
            value = self._data[row][1]
            return QVariant(Qt.Checked if value else Qt.Unchecked)
        return QVariant()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable

    def setData(self, index, value, role):
        if role != Qt.CheckStateRole and role != Qt.EditRole:
            return False
        row = index.row()
        self._data[row][1] = value.toBool()
        return True


class LinksModel(QAbstractListModel):
    def __init__(self, data=[]):
        QAbstractListModel.__init__(self)
        self._data = data

    def rowCount(self, index):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole:
            row = index.row()
            value = self._data[row]
            return QVariant(value)
        elif role == Qt.EditRole:
            row = index.row()
            value = self._data[row]
            return QVariant(value)
        return QVariant()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def setData(self, index, data, role):
        if not index.isValid():
            return False
        row = index.row()
        self._data[row] = unicode(data.toString())
        return True

    def addItem(self, item):
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

    def addItems(self, items):
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data) + len(items))
        self._data += items
        self.endInsertRows()

    def removeItem(self, index):
        log.debug('remove row')
        if not index.isValid():
            return QVariant()
        row = index.row()
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._data[row]
        self.endRemoveRows()

    def removeItems(self, indexes):
        if not indexes:
            return False
        f = indexes[-1].row()
        t = indexes[0].row()
        self.beginRemoveRows(QModelIndex(), f, t)
        for ndx in indexes:
            del self._data[ndx.row()]
        self.endRemoveRows()
        return True


class SEWindow(QMainWindow):

    save_pages = pyqtSignal(list)

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        uic.loadUi("assets/se.ui", self)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        params = settings.STORAGE.get(self.__class__.__name__, {})
        if "state" in params:
            self.restoreState(params["state"])
        if "geometry" in params:
            self.restoreGeometry(params["geometry"])
        self.qty_sb.setValue(params.get('qty', 100))
        self.query_le.setText(params.get('query', 'free proxy list'))
        self.se_lv.setModel(SEModel(params.get('se', searchengines.ENGINES)))

        m = LinksModel([])
        self.sites_lv.setModel(m)
        self.sites_lv.addAction(self.actionDelete)

    @pyqtSlot()
    def on_actionDelete_triggered(self):
        log.debug('delete')
        rows = self.sites_lv.selectedIndexes()
        rows.sort(key=QModelIndex.row, reverse=True)
        self.sites_lv.model().removeItems(rows)

    @pyqtSlot()
    def on_actionStart_triggered(self):
        log.debug('start')
        model = self.sites_lv.model()

        sources = [se[2](unicode(self.query_le.text())) for se in self.se_lv.model()._data if se[1]]

        th = ParseThread(sources, self.qty_sb.value(), self)

        def canceled():
            log.debug('canceled')
            th.process.disconnect()
            th.fail.disconnect()
            th.done.disconnect()
            th.die()

        def process(link):
            model.addItem(link)

        def fail(message):
            d.cancel()
            QMessageBox.critical(self, u'Ошибка', message)

        def done():
            d.cancel()
            QMessageBox.information(self, u'Готово', u'Задание выполнено!')

        th.process.connect(process)
        th.fail.connect(fail)
        th.done.connect(done)

        d = MyProgressDialog(u'Получение выдачи', u'Подключение', u'Отмена', parent=self)
        d.canceled.connect(canceled)
        th.start()
        d.exec_()

    def save(self):
        log.debug('save')
        self.save_pages.emit(self.sites_lv.model()._data)
        self.close()

    def closeEvent(self, event):
        log.debug("close window")
        settings.STORAGE[self.__class__.__name__] = {
            "state": self.saveState(),
            "geometry": self.saveGeometry(),
            'qty': self.qty_sb.value(),
            'query': self.query_le.text(),
            'se': self.se_lv.model()._data,
        }
        event.accept()


if __name__ == '__main__':
    w = SEWindow()
    w.show()
    sys.exit(qApp.exec_())
