'''
@author: javier
'''
from gluon import *

class ContentTypes(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth

    def define_tables(self):
        T = self.T
        db = self.db
        db.define_table('contenttypes',
            Field('contenttype','string',length=100),
            )
        return;
    
    def insert_initial_records(self):
        db = self.db
        if db(db.contenttypes.id > 0).count() == 0:
            db.contenttypes.insert(contenttype='Tab')    
            db.contenttypes.insert(contenttype='Module')
            
        return;