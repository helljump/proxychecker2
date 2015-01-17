#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
import settings
import logging
import copy


log = logging.getLogger(__name__)


DEFAULT = [
    ["http://www.google.com", u"<title>Google</title>"],
    ["http://www.yandex.ru", u"<title>Яндекс</title>"],
    ["http://market.yandex.ru", u"<title>Яндекс.Маркет"],
]


class TargetsModel(QAbstractTableModel):
    def __init__(self, data, parent):
        QAbstractTableModel.__init__(self)
        self.labels = [u"Адрес", u'Фрагмент страницы']
        self._data = data

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self.labels)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole and role != Qt.EditRole:
            return QVariant()
        row = index.row()
        column = index.column()
        if role == Qt.DisplayRole:
            value = self._data[row][column]
            return QVariant(value)
        if role == Qt.EditRole:
            value = self._data[row][column]
            return QVariant(value)
        return QVariant()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.labels[section])
        return QVariant()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def setData(self, index, data, role):
        row = index.row()
        column = index.column()
        self._data[row][column] = unicode(data.toString())
        return True

    def sort(self, col, order):
        reverse = order != Qt.AscendingOrder
        self._data.sort(reverse=reverse)
        ifrom = self.createIndex(0, 0)
        ito = self.createIndex(self.rowCount(None), self.columnCount(None))
        self.dataChanged.emit(ifrom, ito)

    def addItem(self, item):
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

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


class TargetsDialog(QDialog):

    update_targets = pyqtSignal()

    def __init__(self, parent=None):
        super(TargetsDialog, self).__init__(parent)
        uic.loadUi("assets/targets.ui", self)

        params = settings.STORAGE.get(self.__class__.__name__, {})
        if "geometry" in params:
            self.restoreGeometry(params["geometry"])

        egg = copy.deepcopy(DEFAULT)
        m = TargetsModel(settings.STORAGE.get("targets", egg), self)
        self.tableView.setModel(m)
        self.tableView.horizontalHeader().setResizeMode(0, QHeaderView.ResizeToContents)
        self.tableView.addAction(self.actionInsert)
        self.tableView.addAction(self.actionDelete)
        self.tableView.addAction(self.actionReset)

    @pyqtSlot()
    def on_actionDelete_triggered(self):
        log.debug('delete')
        view = self.tableView
        curr = view.currentIndex()
        rows = [ndx for ndx in view.selectedIndexes() if ndx.column() == 0]
        rows.sort(key=QModelIndex.row, reverse=True)
        view.model().removeItems(rows)
        if curr.row() >= len(view.model()._data):
            curr = view.model().createIndex(len(view.model()._data)-1, 0)
        view.setCurrentIndex(curr)
        view.scrollTo(curr)
        self.tableView.model().layoutChanged.emit()

    @pyqtSlot()
    def on_actionInsert_triggered(self):
        log.debug('start')
        self.tableView.model().addItem(['http://', u''])

    @pyqtSlot()
    def on_actionReset_triggered(self):
        log.debug('reset')
        self.tableView.model()._data = copy.deepcopy(DEFAULT)
        self.tableView.model().layoutChanged.emit()

    def accept(self):
        settings.STORAGE['targets'] = self.tableView.model()._data
        self.update_targets.emit()
        self.close()

    def closeEvent(self, event):
        log.debug("close window")
        settings.STORAGE[self.__class__.__name__] = {
            "geometry": self.saveGeometry(),
        }
        event.accept()


if __name__ == '__main__':
    dl = TargetsDialog()
    dl.show()
    sys.exit(qApp.exec_())
