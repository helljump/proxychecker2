#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = "helljump"

APPNAME = 'proxychecker2'

import yaml
import pickle
import logging
import logging.handlers
import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
import atexit
from geoip import GeoIP


from Crypto.Hash import SHA
import win32api
import marshal
from Crypto.Cipher import Blowfish
import types
hash = SHA.new()
d, p = os.path.splitdrive(win32api.GetSystemDirectory())
hash.update(str(win32api.GetSystemInfo()))
hash.update(APPNAME)
hash.update(str(win32api.GetVolumeInformation(d + '/')))
HWINFO = hash.hexdigest()
cipher = Blowfish.new(HWINFO)


if hasattr(sys, "frozen"):
    os.chdir(os.path.dirname(sys.executable))

dbpath = os.path.expanduser('~/proxycheck2')
#dbpath = os.path.expanduser(u'/дурная папка/proxycheck2')
dbpath = unicode(dbpath, encoding=sys.getfilesystemencoding())
if not os.path.isdir(dbpath):
    os.mkdir(dbpath)

'''
try:
    finp = os.path.join(dbpath, 'userdata.pye')
    if os.path.isfile(finp):
        enc = open(finp, 'rb').read()
        data = cipher.decrypt(enc)
        m = types.ModuleType('userdata')
        sys.modules['userdata'] = m
        code = marshal.loads(data)
        exec code in m.__dict__
except:
    log.debug('ohh')
'''

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s: %(message)s")
logname = os.path.expanduser(os.path.join(dbpath, 'proxycheck2.log'))
handler1 = logging.handlers.RotatingFileHandler(logname, maxBytes=100000, backupCount=2)
handler1.setFormatter(formatter)
logger.addHandler(handler1)
if not hasattr(sys, "frozen"):
    handler2 = logging.StreamHandler(sys.stdout)
    handler2.setFormatter(formatter)
    logger.addHandler(handler2)
log = logging.getLogger(__name__)

log1 = logging.getLogger("PyQt4.uic")
log1.setLevel(logging.WARNING)

app = QApplication(sys.argv)
#app.setStyle("cleanlooks")
app.setWindowIcon(QIcon('assets/aaaa32.png'))


## файл настроек
STORAGE = {}
storage_path = os.path.join(dbpath, 'settings.pkl')  # .encode(sys.getfilesystemencoding())
if os.path.isfile(storage_path):
    try:
        STORAGE = pickle.load(open(storage_path, 'r'))
    except:
        log.exception('load settings')


def save_storage():
    pickle.dump(STORAGE, open(storage_path, 'w'))


atexit.register(save_storage)


try:

    CONFIG = {}

    db_version = STORAGE.get('db_version', 1)

    DB = QSqlDatabase.addDatabase("QSQLITE")
    DB.setDatabaseName(os.path.join(dbpath, 'proxy.db'))
    DB.open()

    q = QSqlQuery('CREATE TABLE IF NOT EXISTS proxy (id INTEGER PRIMARY KEY, address TEXT UNIQUE, '
                  'status FLOAT DEFAULT 0.0, type INTEGER DEFAULT -1, anonym INTEGER DEFAULT -1)', DB)
    q.exec_()
    atexit.register(DB.close)

    if db_version < 2:
        log.debug('update base from <2')
        q = QSqlQuery('ALTER TABLE proxy ADD type INTEGER DEFAULT -1', DB)
        q.exec_()
    if db_version < 3:
        log.debug('update base from <4')
        q = QSqlQuery('ALTER TABLE proxy ADD anonym INTEGER DEFAULT -1', DB)
        q.exec_()

    STORAGE['db_version'] = 3

    if getattr(sys, 'frozen', False):
        datadir = os.path.dirname(sys.executable)
    else:
        datadir = os.path.dirname(__file__)
    datadir = unicode(datadir, encoding=sys.getfilesystemencoding())

    GEOIP = GeoIP(os.path.join(datadir, 'assets/GeoIP.dat'))
    FLAGSDIR = os.path.join(datadir, 'assets/flags')

    #COUNTRYDB = QSqlDatabase.addDatabase("QSQLITE", 'country')
    #COUNTRYDB.setDatabaseName(os.path.join(datadir, 'assets/ip2country.db'))
    #COUNTRYDB.open()
    #atexit.register(COUNTRYDB.close)

    #egg = os.path.join(datadir, 'boardposter.yml')
    #CONFIG = yaml.load(codecs.open(egg, "r", "UTF-8"))
    #fname = CONFIG.get('proxyfile')
    #if fname and os.path.isfile(fname):
    #CONFIG['proxy'] = map(unicode.strip, codecs.open('proxy.txt', "r", "UTF-8").readlines())

    egg = os.path.join(datadir, 'assets/headers.yml')
    CONFIG['headers'] = list(yaml.load_all(open(egg, 'r')))


except:
    log.exception('settings error')
