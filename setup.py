#!/usr/bin/env python
#-*- coding: UTF-8 -*-

__author__ = 'helljump'

import sys
from cx_Freeze import setup, Executable
from time import gmtime, strftime


ver = strftime("%y.%m.%d.%H%M", gmtime())


base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name = 'Proxy Checker 2',
    description = 'Proxy Checker 2 by helljump',
    version = ver,
    options = {'build_exe' : {
        'includes' : ['lxml._elementpath', 'gzip', 'dbhash', 'grab.transport.curl'],
        'excludes' : [''],
        'optimize' : 2,
        'silent' : True,
        'copy_dependent_files' : True,
        'include_files' : [
            ('assets','assets'),
            (r'c:\Python26\Lib\site-packages\PyQt4\translations\qt_ru.qm','qt_ru.qm'),
            (r'c:\Python26\Lib\site-packages\requests-2.1.0-py2.6.egg\requests\cacert.pem','cacert.pem'),
            (r'c:\Python26\Lib\site-packages\PyQt4\plugins\sqldrivers','sqldrivers'),
        ],
    }},
    executables = [Executable(
        'proxy_checker.py',
        base = base,
        icon="assets/aaaa32.ico",
        targetName="proxychecker2.exe",
        )]
)
