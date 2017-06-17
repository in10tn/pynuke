# -*- coding: utf-8 -*-

'''
Created on 29/07/2012

@author: javier
'''

from gluon import *
from applications.init.modules import db_pynuke, db_permissions, security
import datetime


class PagePermissions(object):
    def __init__(self):
        from gluon.globals import current
        self.settings = current.settings
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.clpu = db_pynuke.PyNuke.Utils()
        self.cldbper = db_permissions.Permissions()
        self.clsec = security.Security()

    def define_tables(self):
        T = self.T
        db = self.db
        db.define_table(
            'pagepermissions',
            Field('page', db.pages, required=True, label=T('Page')),
            Field('permission', db.permissions, label=T('Permission')),
            Field('allowaccess', 'boolean', label=T('Allow Access')),
            Field('groupid', db.auth_group, requires=IS_EMPTY_OR(IS_IN_DB(db, db.auth_group.id, '%(role)s')) ),
            Field('userid', db.auth_user),
            format='%(page)s',
            plural='pagepermissions',
            singular='pagepermission',
            )

        return

    def insert_initial_records(self):

        return

    def get_pagepermissionsbypageid(self, pageid):
        '''
            Devuelve los permisos que tiene un page
            se usa para construir el menu
        '''

        db = self.db
        result = db(db.pagepermissions.page == pageid).select()

        return result

    def get_pagepermissions_byroleandpage(self, roleid, pageid):
        '''
            Devuelve los permisos que tiene un page para un role
        '''

        db = self.db
        query = (db.pagepermissions.page == pageid)
        query = query & (db.pagepermissions.groupid == roleid)
        result = db(query).select()

        return result

    def all_users_can_read_page(self, pageid):
        db = self.db
        settings = self.settings
        result = False
        perviewpage = settings.perviewpage
        query = (db.pagepermissions.page == pageid)
        query = query & (db.pagepermissions.groupid == None)
        query = query & (db.pagepermissions.permission == perviewpage)
        resultx = db(query).select()
        if len(resultx) > 0:
            result = True
        return result

    def page_has_role_read_permision(self, pageid, roleid):
        #TODO: Mirar en usercanviewpage se puede mejorar, sin repetir codigo...
        '''
            roleid = none para Todos los usuarios
        '''

        db = self.db
        settings = self.settings
        result = False
        perviewpage = settings.perviewpage
        query = (db.pagepermissions.page == pageid)
        query = query & (db.pagepermissions.groupid == roleid)
        query = query & (db.pagepermissions.permission == perviewpage)
        resultx = db(query).select()
        if len(resultx) > 0:
            result = True
        return result

    def user_canviewpage(self, pageid, userid):
        '''

            devuelve True o False en funcion de si un usuario puede ver o no 
            una page según los permisos de la página y la pertenencia a roles
            del usuario.

            Miramos que en los permisos de esa página se encuentre uno de los
            grupos a los que pertenece al usuario con permiso READ y allowaccess
            True

            Los usuarios administradores siempre pueden ver todas las paginas

        '''
        settings = self.settings
        db = self.db
        clsec = self.clsec
        result = False
        perviewpage = settings.perviewpage
        if userid != None:
            if clsec.user_is_admin(userid):
                result = True
            else:
                roles_user = db(db.auth_membership.user_id == userid).select()
                for ru in roles_user:
                    query = (db.pagepermissions.page == pageid)
                    query = query & (db.pagepermissions.groupid == ru.group_id)
                    query = query & (db.pagepermissions.permission == perviewpage)
                    resultx = db(query).select()
                    if len(resultx) > 0:
                        result = True
                        break
                    else:
                        # intentar con el permiso de lectura a todos los usuarios
                        query = (db.pagepermissions.page == pageid)
                        query = query & (db.pagepermissions.groupid == None)
                        query = query & (db.pagepermissions.permission == perviewpage)
                        resultx = db(query).select()
                        if len(resultx) > 0:
                            result = True
                            break
        else:
            # intentar con el permiso de lectura a todos los usuarios
            query = (db.pagepermissions.page == pageid)
            query = query & (db.pagepermissions.groupid == None)
            query = query & (db.pagepermissions.permission == perviewpage)
            resultx = db(query).select()
            if len(resultx) > 0:
                result = True

        return result

    def user_caneditpage(self, pageid, userid):
        '''
            devuelve True o False en funcion de si un usuario puede editar o no
            una page según sus permisos

            miramos que en los permisos de esa página se encuentre uno de los
            grupos a los que pertenece al usuario con permiso READ y allowaccess
            T
        '''
        settings = self.settings
        cldbper = self.cldbper
        db = self.db
        result = False
        pereditpage = settings.pereditpage

        if userid != None:
            roles_user = db(db.auth_membership.user_id == userid).select()
            for ru in roles_user:
                query = (db.pagepermissions.page == pageid)
                query = query & (db.pagepermissions.groupid == ru)
                query = query & (db.pagepermissions.permission == pereditpage)
                resultx = db(query).select()
                if len(resultx) > 0:
                    result = True
                    break

        if not result:
            # intentar con el permiso de lectura a todos los usuarios
            query = (db.pagepermissions.page == pageid)
            query = query & (db.pagepermissions.groupid == None)
            query = query & (db.pagepermissions.permission == pereditpage)
            resultx = db(query).select()
            if len(resultx) > 0:
                result = True

        return result

    def is_page_visible(self, objpag):
        # Se utiliza en el sitemap y para ver si se pone en el menú
        settings = self.settings
        auth = self.auth
        clpu = self.clpu
        pagina_visible = False
        tnow = datetime.datetime.now()
        if clpu.is_in_interval_of_dates(tnow, objpag.startdate,
                                            objpag.enddate):
            pagina_visible = objpag.isvisible

        return pagina_visible
