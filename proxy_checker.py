#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import sys
from PyQt4.QtCore import *
from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4 import QtGui
from PyQt4.QtSql import *
from PyQt4 import uic
import settings
import logging
import pages_parser
#import bcryptor
import targets_editor
import se_parser
import os
import proxytest
import Queue
import random
import time
import shutil
import types
from setup_dlg import SetupDialog
from win32api import GetFileVersionInfo, LOWORD, HIWORD


log = logging.getLogger(__name__)


class Task(object):
    pass


class CheckThread(pages_parser.MyThread):

    process = pyqtSignal(Task)

    def __init__(self, queue, parent):
        super(CheckThread, self).__init__(parent)
        self.queue = queue
        self.checker = None

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        for task in iter(self.queue.get, "STOP"):
            if not self.checker:
                self.checker = proxytest.CurlChecker([task.target, task.tag], task.timeout)
            log.debug(u"process %s by(%s)", task.addr, QThread.currentThread())
            try:
                task.status, task.type_ = self.checker(task.addr)
                time.sleep(1)
                #task.status = random.random()
                log.debug("success %s %f %d", task.addr, task.status, task.type_)
            except Exception:
                task.status = -1
                task.type_ = -1
                log.exception("catched in thread")
            self.process.emit(task)
            self.queue.task_done()
            if not self.active:
                break
        log.debug("stop %s" % QThread.currentThread())


class ImportThread(pages_parser.MyThread):

    done = pyqtSignal(QString)
    fail = pyqtSignal(QString)

    def __init__(self, fname, parent):
        super(ImportThread, self).__init__(parent)
        self.fname = fname

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        try:
            self.job()
        except Exception, err:
            log.exception("import thread")
            self.fail.emit(pages_parser.to_text(err))
        log.debug("stop %s" % QThread.currentThread())

    def job(self):
        if not self.fname or not os.path.isfile(self.fname):
            self.fail.emit(u'Не удалось открыть файл')
            return
        items = map(str.strip, open(self.fname, "r").readlines())
        settings.DB.transaction()
        q = QSqlQuery('insert into proxy (address) values (:addr)', settings.DB)
        for item in items:
            q.bindValue(':addr', item)
            q.exec_()
            if not self.active:
                settings.DB.rollback()
                break
        settings.DB.commit()
        self.done.emit(u'Импорт выполнен.')


class ClearThread(pages_parser.MyThread):

    done = pyqtSignal(QString)
    fail = pyqtSignal(QString)

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        try:
            self.job()
        except Exception, err:
            log.exception("clear thread")
            self.fail.emit(pages_parser.to_text(err))
        log.debug("stop %s" % QThread.currentThread())

    def job(self):
        q = QSqlQuery('DELETE FROM proxy WHERE status<0', settings.DB)
        q.exec_()
        self.done.emit(u'Очистка выполнена.')


class ExportThread(pages_parser.MyThread):

    done = pyqtSignal(QString)
    fail = pyqtSignal(QString)

    def __init__(self, fname, parent):
        super(ExportThread, self).__init__(parent)
        self.fname = fname

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        try:
            self.job()
        except Exception, err:
            log.exception("clear thread")
            self.fail.emit(pages_parser.to_text(err))
        log.debug("stop %s" % QThread.currentThread())

    def job(self):
        with open(self.fname, 'w') as fout:
            q = QSqlQuery('SELECT address FROM proxy', settings.DB)
            while q.next():
                addr = q.value(0).toString()
                fout.write(addr + '\n')
            self.done.emit(u'Выгрузка выполнена.')


def get_version_number():
    try:
        info = GetFileVersionInfo(sys.executable, "\\")
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        return HIWORD(ms), LOWORD(ms), HIWORD(ls), LOWORD(ls)
    except:
        return 0, 0, 0, 0


'''
class AboutDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.ver_le.setText('.'.join(map(str, get_version_number())))
'''


class AboutDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        uic.loadUi("assets/about.ui", self)
        #self.setupUi(self)
        try:
            m = __import__('BUILD_CONSTANTS')
            self.ver_le.setText(m.BUILD_TIMESTAMP)
        except ImportError, err:
            log.debug('%s', err)
        self.hw_le.setText(settings.HWINFO)

    @QtCore.pyqtSlot()
    def on_reg_pb_clicked(self):
        log.debug('reg')
        fn = QtGui.QFileDialog.getOpenFileName(self, u'Регистрация', filter=u'Proxy Checker 2 ключ (*.pye)')
        if fn.isEmpty():
            return
        shutil.copy(unicode(fn), os.path.join(settings.dbpath, 'userdata.pye'))
        QtGui.QMessageBox.information(self, u'Регистрация', u'Ключ установлен. Пожалуйста, перезагрузите программу.')


class RegistrationDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        uic.loadUi("assets/registration.ui", self)

    def accept(self):
        egg = unicode(self.plainTextEdit.toPlainText())
        settings.STORAGE['registration'] = egg
        self.close()


class ProxyModel(QSqlTableModel):

    TYPES = {0: 'HTTP', 4: 'SOCKS4', 5: 'SOCKS5'}

    def __init__(self, parent, db):
        QSqlTableModel.__init__(self, parent, db)
        self.setEditStrategy(QSqlTableModel.OnFieldChange)
        #self.cq = QSqlQuery('SELECT full FROM country WHERE start<=? AND end>=?',
        #    settings.COUNTRYDB)
        self.couflags = {
            'unknown': QIcon(os.path.join(settings.FLAGSDIR, 'unknown.png'))
        }

    #def columnCount(self, parent):
    #    return 6

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        #row = index.row()
        column = index.column()
        if role == Qt.DisplayRole and column == 2:
            v, rc = QSqlTableModel.data(self, index, role).toFloat()
            if v < 0:
                value = u'не отвечает'
            elif v == 0:
                value = u'не тестировался'
            else:
                value = v
            return QVariant(value)
        elif role == Qt.DisplayRole and column == 3:
            v, rc = QSqlTableModel.data(self, index, role).toInt()
            if rc:
                return QVariant(self.TYPES.get(v, ''))
        elif role == Qt.DisplayRole and column == 4:
            v, rc = QSqlTableModel.data(self, index, role).toInt()
            if v < 0:
                value = u'неизвестно'
            else:
                value = u'..'
            return QVariant(value)
        elif column == 1 and role == Qt.DecorationRole:
            v = index.data(Qt.DisplayRole).toString()
            addr, port = unicode(v).split(':')
            spam = settings.GEOIP.country(addr)
            if spam not in self.couflags:
                fname = os.path.join(settings.FLAGSDIR, spam + '.png')
                if os.path.isfile(fname):
                    icon = QIcon(fname)
                    self.couflags[spam] = icon
                else:
                    spam = 'unknown'
            return QVariant(self.couflags[spam])
        return QSqlTableModel.data(self, index, role)

    def flags(self, index):
        egg = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == 1:  # only ip addr
            egg |= Qt.ItemIsEditable
        return egg

    def setData(self, index, data, role):
        if index.column() == 1:
            ndx = self.createIndex(index.row(), 2)
            QSqlTableModel.setData(self, ndx, QVariant(0), role)
            log.debug('reset status')
        return QSqlTableModel.setData(self, index, data, role)


class TargetsModel(QStringListModel):
    def __init__(self, parent, targets):
        QStringListModel.__init__(self, parent)
        self._data = targets

    def rowCount(self, index):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            value = self._data[index.row()][0]
            return QVariant(value)
        return QVariant()

    def getTarget(self, row):
        return self._data[row]


class CheckerWindow(QMainWindow):

    V = 'sdvvuh*^Glksasal@#^vicysa789444476@@@^df86cq)(*&wefg8od6'

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        uic.loadUi("assets/proxy.ui", self)

        params = settings.STORAGE.get(self.__class__.__name__, {})
        if "state" in params:
            self.restoreState(params["state"])
        if "geometry" in params:
            self.restoreGeometry(params["geometry"])

        #self.hasher = bcryptor.Bcrypt()

        targets = settings.STORAGE.get("targets", targets_editor.DEFAULT)
        model = TargetsModel(self, targets)
        self.target_cb.setModel(model)

        spam = params.get("target", 0)
        egg = self.target_cb.count()
        if spam >= egg:
            self.target_cb.setCurrentIndex(0)
        else:
            self.target_cb.setCurrentIndex(spam)

        self.threads_sb.setValue(params.get("threads", 3))
        self.timeout_sb.setValue(params.get("timeout", 30))

        '''
        try:
            u = __import__('userdata')
            self.sublink = types.MethodType(u.sublink, self)
        except ImportError:
            self.setWindowTitle(self.windowTitle() + u'(Незарегистрирован)')
            self.menubar.addAction(self.actionBuy)
        '''

        model = ProxyModel(self, settings.DB)
        model.setTable("proxy")
        model.select()
        #while model.canFetchMore():
        #    model.fetchMore()
        model.setHeaderData(1, Qt.Horizontal, u'Адрес')
        model.setHeaderData(2, Qt.Horizontal, u'Статус')
        model.setHeaderData(3, Qt.Horizontal, u'Тип')
        model.setHeaderData(4, Qt.Horizontal, u'Анонимность')
        #model.setHeaderData(5, Qt.Horizontal, u'Страна')

        self.tableView.setModel(model)
        self.tableView.hideColumn(0)
        self.tableView.hideColumn(4)
        self.tableView.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.tableView.addAction(self.actionStartSelected)
        self.tableView.addAction(self.actionDelete)

    @pyqtSlot()
    def on_actionBuy_triggered(self):
        url = QUrl('http://blap.ru/poleznye-skripty/proxy-checker-2/')
        QDesktopServices.openUrl(url)

    @pyqtSlot()
    def on_actionSetup_triggered(self):
        dlg = SetupDialog(self)
        dlg.exec_()

    @pyqtSlot()
    def on_actionClear_triggered(self):
        log.debug('clear')
        th = ClearThread(self)
        dl = se_parser.MyProgressDialog(u'Очиста', u'Удаление дохлых прокси', u'Отмена', parent=self)

        def canceled():
            th.fail.disconnect()
            th.done.disconnect()
            th.die()

        def fail(message):
            dl.cancel()
            QMessageBox.critical(self, u'Ошибка', message)

        def done(message):
            model = self.tableView.model()
            model.select()
            while model.canFetchMore():
                model.fetchMore()
            dl.cancel()
            QMessageBox.information(self, u'Готово', message)
        th.fail.connect(fail)
        th.done.connect(done)
        dl.canceled.connect(canceled)
        th.start()
        dl.show()

    @pyqtSlot()
    def on_actionDelete_triggered(self):
        log.debug('delete')
        model = self.tableView.model()
        rows = [ndx for ndx in self.tableView.selectedIndexes() if ndx.column() == 1]
        rows.sort(key=QModelIndex.row, reverse=True)
        settings.DB.transaction()
        for ndx in rows:
            model.removeRow(ndx.row())
        settings.DB.commit()
        log.debug('del done')

    @pyqtSlot()
    def on_actionStart_triggered(self):
        log.debug('start all')
        egg = []
        q = QSqlQuery('SELECT address FROM proxy', settings.DB)
        while q.next():
            addr = q.value(0).toString()
            egg.append(unicode(addr))
        self.startCheck(egg)

    def sublink(self, rows):
        #random.shuffle(rows)
        return rows#[:10]

    @pyqtSlot()
    def on_actionStartSelected_triggered(self):
        log.debug('start selected')
        egg = []
        for ndx in self.tableView.selectedIndexes():
            if ndx.column() == 1:
                v = ndx.data(Qt.DisplayRole).toString()
                egg.append(unicode(v))
        self.startCheck(egg)

    def startCheck(self, data):
        log.debug('check %i', len(data))
        threads = []
        model = self.tableView.model()
        rows = self.sublink(data)
        d = se_parser.MyProgressDialog(u'Проверка', u'Обработка списка', u'Отмена', 1, len(rows),
                                       parent=self)
        #d = CheckWindow(u'Проверка', u'Обработка списка', u'Отмена', 1, len(rows), parent=self)
        log.debug('total rows %i', len(rows))

        def canceled():
            log.debug('canceled')
            for th in threads:
                th.process.disconnect()
                th.die(False)
            log.debug('update model')
            model.select()
        d.canceled.connect(canceled)
        d.show()
        queue = Queue.Queue()
        egg = self.target_cb.currentIndex()
        target, tag = self.target_cb.model().getTarget(egg)
        donez = []
        for row in rows:
            task = Task()
            task.addr, task.timeout = str(row), self.timeout_sb.value()
            task.target, task.tag, task.status = str(target), unicode(tag), 0.0
            queue.put(task)
        q = QSqlQuery('update proxy set status=?, type=? where address=?', settings.DB)

        def process(task):
            q.bindValue(0, task.status)
            q.bindValue(1, task.type_)
            q.bindValue(2, task.addr)
            q.exec_()
            d.incValue()
            if task.status <= 0.0:
                d.setText(u'%s: не отвечает' % task.addr)
            else:
                d.setText(u'%s: %.2fс %s' % (task.addr, task.status, ProxyModel.TYPES[task.type_]))
            donez.append(task.addr)

        def done():
            if not queue.empty():
                return
            model.select()
            d.cancel()
            #QMessageBox.information(self, u'Проверка',
            #    u'Задание выполнено. %i адресов проверено.' % len(donez))
        for i in range(self.threads_sb.value()):
            queue.put("STOP")
            th = CheckThread(queue, self)
            th.finished.connect(done)
            th.process.connect(process)
            th.start()
            threads.append(th)

    @pyqtSlot()
    def on_actionImport_triggered(self):
        log.debug('import')
        fname = QFileDialog.getOpenFileName(self, u"Импорт", ".", u"список адресов (*.txt)")
        if not fname:
            return
        fname = unicode(fname)
        th = ImportThread(fname, self)
        dl = se_parser.MyProgressDialog(u'Импорт', u'Загрузка адресов', u'Отмена', parent=self)

        def canceled():
            th.fail.disconnect()
            th.done.disconnect()
            th.die()

        def fail(message):
            dl.cancel()
            QMessageBox.critical(self, u'Ошибка', message)

        def done(message):
            self.tableView.model().select()
            dl.cancel()
            QMessageBox.information(self, u'Готово', message)
        th.fail.connect(fail)
        th.done.connect(done)
        dl.canceled.connect(canceled)
        th.start()
        dl.show()

    @pyqtSlot()
    def on_actionExport_triggered(self):
        log.debug('export')
        fname = QFileDialog.getSaveFileName(self, u"Экспорт", ".", u"список адресов (*.txt)")
        if not fname:
            return
        fname = unicode(fname)
        th = ExportThread(fname, self)
        dl = se_parser.MyProgressDialog(u'Экспорт', u'Выгрузка адресов', u'Отмена', parent=self)

        def canceled():
            th.fail.disconnect()
            th.done.disconnect()
            th.die()

        def fail(message):
            dl.cancel()
            QMessageBox.critical(self, u'Ошибка', message)

        def done(message):
            self.tableView.model().select()
            dl.cancel()
            QMessageBox.information(self, u'Готово', message)
        th.fail.connect(fail)
        th.done.connect(done)
        dl.canceled.connect(canceled)
        th.start()
        dl.show()

    @pyqtSlot()
    def on_actionParser_triggered(self):
        log.debug('pages')
        try:
            w = pages_parser.PagesWindow(self)
            w.update_proxy.connect(self.update_proxy)
            w.show()
        except:
            log.exception('open pages exception')

    def update_proxy(self):
        log.debug('update proxies')
        self.tableView.model().select()

    @pyqtSlot()
    def on_actionAbout_triggered(self):
        log.debug('about')
        dl = AboutDialog(self)
        dl.show()

    @pyqtSlot()
    def on_actionExit_triggered(self):
        log.debug('exit')
        self.close()

    @pyqtSlot()
    def on_actionTargets_triggered(self):
        log.debug('targets')
        dl = targets_editor.TargetsDialog(self)
        dl.update_targets.connect(self.update_targets)
        dl.show()

    @pyqtSlot()
    def on_actionRegistration_triggered(self):
        log.debug('registration')
        dl = RegistrationDialog(self)
        dl.show()

    def update_targets(self):
        log.debug('update targets')
        self.target_cb.setCurrentIndex(0)
        model = self.target_cb.model()
        model._data = settings.STORAGE["targets"]
        model.layoutChanged.emit()

    def closeEvent(self, event):
        log.debug("close window")
        settings.STORAGE[self.__class__.__name__] = {
            "state": self.saveState(),
            "geometry": self.saveGeometry(),
            "threads": self.threads_sb.value(),
            "target": self.target_cb.currentIndex(),
            "timeout": self.timeout_sb.value(),
        }
        event.accept()


if __name__ == '__main__':
    w = CheckerWindow()
    w.show()
    sys.exit(qApp.exec_())
