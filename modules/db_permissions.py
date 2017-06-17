# -*- coding: utf-8 -*-

'''
Created on 29/07/2012

@author: javier
'''

from gluon import *


class Permissions(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth

    def define_tables(self):
        T = self.T
        db = self.db
        db.define_table(
            'permissions',
            Field('name','string',label=T('Name')),
            Field('code','string'),
            Field('moduledefid',db.moduledefinitions, requires=IS_EMPTY_OR(IS_IN_DB(db, db.moduledefinitions.id, '%(friendlyname)s'))),
            Field('perm_key','string'),
            Field('sortable','integer'),
            )

        return

    def insert_initial_records(self):
        db = self.db
        permission_view_page = db.permissions.insert(name='View Page',
                                                 code='SYSTEM_PAGE',
                                                 perm_key='View',
                                                 sortable=0)

        permission_edit_page = db.permissions.insert(name='Edit Page',
                                                code='SYSTEM_PAGE',
                                                perm_key='Edit',
                                                sortable=9999)

        return permission_view_page, permission_edit_page

    def editar(self, tab_id):
        '''
            devuelve un formulario para editar un tab en Ajax
        '''
        T = self.T
        db = self.db

        fields = ['name', 'title', 'isvisible', 'disablelink',
                  'issecure']

        submit_button = T('Update')
        record = db.tabs[tab_id]

        #http://stackoverflow.com/questions/476426/submit-an-html-form-with-empty-checkboxes
        result = SQLFORM(db.tabs, record, fields=fields,
                         submit_button=submit_button,
                         hidden=dict(isvisible='F', issecure='F',
                                     disablelink='F'))

        return result

    def nuevo(self):
        '''
            devuelve un formulario para crear una nueva pagina
        '''
        T = self.T
        db = self.db
        submit_button = T('Add Page')
        return SQLFORM(db.tabs,
                       submit_button=submit_button

                       )

    def get_permissionid_by_codeandkey(self, code, key):
            """
                Averigua el id de un permiso a partir del campo code
                Se consulta en la base de datos por ese registro

                Parametros
                ----------
                code:
                    code del permission
                key:
                    key del permission

                Devuelve
                -------
                el id del permission o -1 si no hay nada coincidente

            """
            db = self.db
            result = -1
            query = (db.permissions.code == code)
            query = query & (db.permissions.perm_key == key)
            rec_result = db(query).select().first()
            if rec_result != None:
                result = rec_result.id
            return result

    def rol_has_permission(self,rolid, pageid, permission):
        '''
            Devuelve True o False según si el rol especificado tiene o no el
            permiso especificado para la pagina dada.
        '''
        result = False
        db = self.db
        query = (db.pagepermissions.page == pageid)
        query = query & (db.pagepermissions.groupid == rolid)
        query = query & (db.pagepermissions.permission == permission)
        resultx = db(query).select()
        if len(resultx) > 0:
            result = True
        return result
