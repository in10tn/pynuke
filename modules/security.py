# -*- coding: utf-8 -*-

'''
Created on 29/07/2012

@author: javier
'''

from gluon import *
import db_options,db_pynuke
import uuid
import datetime


class Security(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.settings = current.settings

    def user_has_tab_readpermissions(self,tabid,userid):

        #devuelve True o False en funcion de si puede ver o no un tab

        db = self.db
        result = False
#        auth = self.auth
#        roles_user = db(db.auth_membership.user_id==userid).select()
#        (auth.has_membership(role = settings.admin_role_name))
        return result

    def user_can_view_controlpanel(self,userid):
        ''' El panel de control solo es visible por los usuarios que pertenecen 
            al grupo "Administradores"
        '''
        return db_pynuke.PyNuke.Utils().bool2str(self.user_is_admin(userid))

    def user_is_admin(self, userid):
        settings = current.settings
        auth = self.auth
        arn = settings.admin_role_name
        valor = False
        if (auth.user_id != None) and ((auth.has_membership(role=arn))):
            valor = True

        return valor
