#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"


import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtSql import *
import settings
import logging
import se_parser
from se_parser import MyProgressDialog
import os
import Queue
import pages


log = logging.getLogger(__name__)


def to_text(err):
    '''конвертит текст исключения в unicode'''
    message = 'unknown'
    try:
        message = unicode(err)
        log.debug('exception in unicode')
    except UnicodeDecodeError:
        message = str(err).decode('cp1251', 'replace')
        log.debug('exception in str')
    except Exception:
        log.exception("exception unknown")
    return message


class MyThread(QThread):

    def __init__(self, parent):
        super(MyThread, self).__init__(parent)
        self.active = True

    def die(self, wait=False):
        self.active = False
        if wait:
            self.wait(100)
            self.terminate()
        log.debug("die %s" % QThread.currentThread())


class ParseThread(MyThread):

    process = pyqtSignal(QString)
    done = pyqtSignal()
    fail = pyqtSignal(QString)

    def __init__(self, queue, parent):
        super(ParseThread, self).__init__(parent)
        self.queue = queue

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        for page in iter(self.queue.get, "STOP"):
            page = unicode(page)
            log.debug(u"process %s by(%s)", page, QThread.currentThread())
            try:
                for proxy in pages.parse(page):
                    self.process.emit(proxy)
            except Exception:
                log.exception("catched in thread")
            if not self.active:
                break
            self.queue.task_done()
        self.done.emit()
        log.debug("stop %s" % QThread.currentThread())


class FilterThread(MyThread):

    process = pyqtSignal(se_parser.LinksModel)
    done = pyqtSignal()
    fail = pyqtSignal(QString)

    def __init__(self, models, parent):
        super(FilterThread, self).__init__(parent)
        self.models = models

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        try:
            for model in self.models:
                egg = list(set(model._data))
                egg.sort()
                model._data = egg
                self.process.emit(model)
                if not self.active:
                    break
        except Exception:
            log.exception("filter thread")
        self.done.emit()
        log.debug("stop %s" % QThread.currentThread())


class ImportThread(MyThread):

    done = pyqtSignal(list)
    fail = pyqtSignal(QString)

    def __init__(self, fname, parent):
        super(ImportThread, self).__init__(parent)
        self.fname = fname

    def run(self):
        log.debug("start %s" % QThread.currentThread())
        try:
            if self.fname and os.path.isfile(self.fname):
                items = map(str.strip, open(self.fname, "r").readlines())
            else:
                items = []
            self.done.emit(items)
        except Exception, err:
            log.exception("import thread")
            self.fail.emit(to_text(err))
        log.debug("stop %s" % QThread.currentThread())


class PagesWindow(QMainWindow):

    update_proxy = pyqtSignal()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        uic.loadUi("assets/pages.ui", self)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        params = settings.STORAGE.get(self.__class__.__name__, {})
        if "state" in params:
            self.restoreState(params["state"])
        if "geometry" in params:
            self.restoreGeometry(params["geometry"])
        self.threads_sb.setValue(params.get('threads', 3))

        d = settings.STORAGE.get('pages', [])
        m1 = se_parser.LinksModel(d)
        self.sites_lv.setModel(m1)
        self.sites_lv.addAction(self.actionDelete)

        m2 = se_parser.LinksModel()
        self.proxy_lv.setModel(m2)
        self.proxy_lv.addAction(self.actionDelete)

    @pyqtSlot()
    def on_actionStart_triggered(self):
        log.debug('parse')
        threads = []
        queue = Queue.Queue()
        pages = self.sites_lv.model()._data
        d = MyProgressDialog(u'Парсинг', u'Подключение...', u'Отмена', parent=self)

        def canceled():
            log.debug('canceled')
            for th in threads:
                th.die()
                th.process.disconnect()
                th.done.disconnect()

        def process(proxy):
            self.proxy_lv.model().addItem(proxy)
            d.setLabelText(proxy)

        def done():
            if not queue.empty():
                return
            d.cancel()
            QMessageBox.information(self, u'Парсинг', u'Задание выполнено!')

        for page in pages:
            queue.put(page)

        for i in range(self.threads_sb.value()):
            th = ParseThread(queue, self)
            th.done.connect(done)
            th.process.connect(process)
            th.start()
            threads.append(th)
            queue.put("STOP")

        d.canceled.connect(canceled)
        d.show()

    @pyqtSlot()
    def on_actionFilter_triggered(self):
        log.debug('filter')
        models = [self.sites_lv.model(), self.proxy_lv.model()]
        th = FilterThread(models, self)
        d = MyProgressDialog(u'Обработка', u'Удаление дублей', u'Отмена', 1, len(models), parent=self)

        def canceled():
            log.debug('canceled')
            th.fail.disconnect()
            th.process.disconnect()
            th.done.disconnect()
            th.die()

        def fail(message):
            d.cancel()
            QMessageBox.critical(self, u'Ошибка', message)

        def process(model):
            model.layoutChanged.emit()
            d.setValue(d.value() + 1)

        def done():
            d.cancel()
            QMessageBox.information(self, u'Обработка', u'Задание выполнено!')
        th.fail.connect(fail)
        th.done.connect(done)
        th.process.connect(process)
        d.canceled.connect(canceled)
        th.start()
        d.show()

    @pyqtSlot()
    def on_actionDelete_triggered(self):
        log.debug('delete')
        if self.sites_lv.hasFocus():
            view = self.sites_lv
        elif self.proxy_lv.hasFocus():
            view = self.proxy_lv
        else:
            return
        curr = view.currentIndex()
        rows = view.selectedIndexes()
        rows.sort(key=QModelIndex.row, reverse=True)
        view.model().removeItems(rows)
        if curr.row() >= len(view.model()._data):
            curr = view.model().createIndex(len(view.model()._data)-1, 0)
        view.setCurrentIndex(curr)
        view.scrollTo(curr)

    @pyqtSlot()
    def on_actionImport_triggered(self):
        fname = QFileDialog.getOpenFileName(self, u"Импорт", ".", u"список страниц (*.txt)")
        if not fname:
            return
        fname = unicode(fname)
        th = ImportThread(fname, self)
        dl = MyProgressDialog(u'Импорт', u'Загрузка страниц', u'Отмена', parent=self)

        def canceled():
            th.fail.disconnect()
            th.done.disconnect()
            th.die()

        def fail(message):
            dl.cancel()
            QMessageBox.critical(self, u'Ошибка', message)

        def done(items):
            self.sites_lv.model().addItems(items)
            dl.cancel()
            QMessageBox.information(self, u'Готово', u'Задание выполнено!')
        th.fail.connect(fail)
        th.done.connect(done)
        dl.canceled.connect(canceled)
        th.start()
        dl.show()

    @pyqtSlot()
    def on_actionSearch_triggered(self):
        w = se_parser.SEWindow(self)
        w.save_pages.connect(self.set_pages)
        w.show()

    def set_pages(self, data):
        log.debug('add %i pages', len(data))
        self.sites_lv.model().addItems(data)

    def save(self):
        log.debug('save')
        settings.STORAGE['pages'] = self.sites_lv.model()._data

        settings.DB.transaction()
        q = QSqlQuery('insert into proxy (address) values (:addr)', settings.DB)
        for addr in self.proxy_lv.model()._data:
            q.bindValue(':addr', addr)
            q.exec_()
        settings.DB.commit()
        self.update_proxy.emit()

        self.close()

    def closeEvent(self, event):
        log.debug("close window")
        settings.STORAGE[self.__class__.__name__] = {
            "state": self.saveState(),
            "geometry": self.saveGeometry(),
            "threads": self.threads_sb.value(),
        }
        event.accept()


if __name__ == '__main__':
    w = PagesWindow()
    w.show()
    sys.exit(qApp.exec_())
