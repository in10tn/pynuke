# -*- coding: utf-8 -*-
'''
Created on 24/01/2012

@author: javier
'''
from gluon import *
#import db_options

class UserRegistrations(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth

    def define_tables(self):
        T = self.T
        db = self.db
        db.define_table('userregistrations',
            Field('Type','string',length=100),
            )
        
        if db(db.userregistrations.id > 0).count() == 0:
            db.userregistrations.insert(Type=T('None'))
            db.userregistrations.insert(Type=T('Private'))
            db.userregistrations.insert(Type=T('Public'))
            db.userregistrations.insert(Type=T('Verified'))        
        return;
    
    def ver_users(self):     
        db=self.db
        
        tabla = db.auth_user                       
        editable=True
        deletable = True
        orderby=''
        links =[]
        #maxtextlength=20
        headers = {}
        field_id = None
        left=[]
        fields = None
        showbuttontext=True 
        linked_tables = None
        oncreate = None
        onupdate = None    
        ondelete = None
        details = True
        searchable = True
        csv= True
        create = True
        grid_result = SQLFORM.grid
        maxtextlengths={}
                
        grid = grid_result(db[tabla],
                                oncreate = oncreate,
                                onupdate = onupdate,
                                ondelete = ondelete,
                                searchable = searchable,
                                deletable = deletable,
                                create = create,
                                details = details,
                                showbuttontext=showbuttontext,
                                links=links,
                                csv = csv,                             
        #                            maxtextlength=maxtextlength,
                                maxtextlengths=maxtextlengths,
                                headers=headers,
                                editable=editable,
                                left=left,
                                fields=fields,
                                field_id=field_id, 
                                #linked_tables = linked_tables,
                                orderby=orderby,
                                user_signature=False,                                
                                #ui = 'web2py'                                                   
                                )
        
        
        return dict(grid=grid)
 