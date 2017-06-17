#!/usr/bin/env python
# encoding: utf-8
# Requiere instalar http://pyyaml.org/wiki/PyYAML
from applications.init.modules.plugin_ckeditor import CKEditor
from gluon import *
import yaml
import os.path
from applications.init.modules import db_pynuke
class Redirects(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth

    def define_tables(self):
        T = self.T
        db = self.db
        db.define_table('redirects_301',
            Field('url_in', length = 255, required=True,unique=True),
            Field('url_out',required=True),
            format='%(url_in)s',
            plural='redirects',
            singular='redirect'    
                    )        
        return;
    
    def show_grid_params(self,view,):
        '''
        Esta función devuelve los valores necesarios para mostrar el Smartgrid
        en el controlador Auxiliares.py
        '''
        
        maxtextlengths = {'options.id':10,
                          'option.name':50,
                          'option.value':50,
                         }
        deletable = False

        return maxtextlengths,deletable

    def ver(self):
        # redirect list
        db = self.db
        query = (db.redirects_301.id > 0)
        fields = [db.redirects_301.id, db.redirects_301.url_in,
                  db.redirects_301.url_out]
        maxtextlengths = {'redirects_301.id': 8,
                          'redirects_301.url_in': 90,
                          'redirects_301.url_out': 80,
                          }
        table = SQLFORM.grid(query,
                             fields=fields,
                             maxtextlengths=maxtextlengths,
                             orderby=db.redirects_301.id,
                             csv=True,
                             searchable=True,
                             create=True,
                             editable=True,
                             details=False,
                             deletable=True,
                             user_signature=True)
        return table
    
    def editar(self,redirect_id):       
        '''
            devuelve un formulario para editar un redirect
        '''        
        sepuedeborrar = True
        db=self.db
        record=db.redirects_301[redirect_id]        
        return SQLFORM(db.redirects_301, record,
                         deletable=sepuedeborrar)    