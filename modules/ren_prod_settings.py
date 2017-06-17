# -*- coding: utf-8 -*-
from gluon.storage import Storage
settings = Storage()
settings.migrate = True
#settings.database_uri = 'mysql://usrdbpynuke:pwddbpynuke@localhost/pynuke_dev'
settings.database_uri = 'sqlite://storage.sqlite4'
