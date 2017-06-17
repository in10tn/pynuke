# -*- coding: utf-8 -*-
import os
from gluon import *
from plugin_ckeditor import CKEditor


if False:
    from gluon.tools import *
    from gluon import *
    db = DAL()
    auth = Auth(db)
    request, session, response, T, cache = current.request, current.session, \
                                     current.response, current.t, current.cache
    db = current.db
    settings = current.settings
    auth = Auth(db, hmac_key=Auth.get_or_create_key())
    crud, service, plugins = Crud(db), Service(), PluginManager()


@auth.requires_membership(settings.admin_role_name)
def upload():
    (new_filename, old_filename, length, mime_type) = current.plugin_ckeditor.handle_upload()

    title = os.path.splitext(old_filename)[0]

    result = db.plugin_ckeditor_upload.validate_and_insert(
        title = title,
        filename = old_filename,
        upload = new_filename,
        length = length,
        mime_type = mime_type
    )

    text = ''
    url = URL('static', 'uploads', args=[new_filename])
    
    if not result.id:
        text = result.errors

    return dict(text=text, cknum=request.vars.CKEditorFuncNum, url=url)

@auth.requires_membership(settings.admin_role_name)      
def browse():
    db = current.plugin_ckeditor.db
    table_upload = db.plugin_ckeditor_upload
    browse_filter = current.plugin_ckeditor.settings.browse_filter
    set = db(table_upload.id>0)
    for key, value in browse_filter.items():
        if value[0] == '<':
            set = set(table_upload[key]<value[1:])
        elif value[0] == '>':
            set = set(table_upload[key]>value[1:])
        elif value[0] == '!':
            set = set(table_upload[key]!=value[1:])
        else:
            set = set(table_upload[key]==value)
    
    rows = set.select(orderby=table_upload.title)
    
    return dict(rows=rows, cknum=request.vars.CKEditorFuncNum)

@auth.requires_membership(settings.admin_role_name)
def delete():
    filename = request.args(0)
    if not filename:
        raise HTTP(401, 'Required argument filename missing.')
        
    db = current.plugin_ckeditor.db
    table_upload = db.plugin_ckeditor_upload
    db(table_upload.upload==filename).delete()
    
    # delete the file from storage
    path = os.path.join(request.folder,'static', 'uploads', filename)
    os.unlink(path)