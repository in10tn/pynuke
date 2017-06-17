# -*- coding: utf-8 -*-
# This plugins is licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
# Authors: Yusuke Kishita <yuusuuke.kishiita@gmail.com>, Kenji Hosoda <hosoda@s-cubism.jp>
from gluon import *
from applications.init.modules import db_pages
# For referencing static and views from other application
import os
APP = os.path.basename(os.path.dirname(os.path.dirname(__file__)))


class JsTree(object):

    def __init__(self, tree_model, renderstyle=False):        
        self.tree_model = tree_model  # tree_model could be an MPTT object of plugin_mptt

        _urls = [URL(APP, 'static', 'plugin_jstree/jstree/jquery.hotkeys.js'),
                 URL(APP, 'static', 'plugin_jstree/jstree/jquery.jstree.js')]
        if renderstyle:
            _urls.append(URL(APP, 'static', 'plugin_jstree/main.css'))
        for _url in _urls:
            if _url not in current.response.files:
                current.response.files.append(_url)

        self.db = current.db

    def recordbutton(self, buttonclass, buttontext, buttonurl,
                     showbuttontext=True, **attr):
        if showbuttontext:
            inner = SPAN(buttontext, _class='ui-button-text')
        else:
            inner = SPAN(XML('&nbsp'), _style='padding: 0px 7px 0px 6px;')
        return A(SPAN(_class='ui-icon ' + buttonclass),
                 inner,
                 _title=buttontext, _href=buttonurl, _class='ui-btn', **attr)

    def build_tree_objects(self, initially_select):
        initially_open = []
        data = []

        for child in self.tree_model.descendants_from_node(initially_select, include_self=True,
                                                           onlyvisibles=False,
                                                           onlyactivated=False
                                                           ).select(orderby=self.tree_model.desc):
            node_el_id = 'node_%s' % child.id
            if not self.tree_model.is_leaf_node(child):
                initially_open.append(node_el_id)
            if child.level == 0:
                data.append(dict(data=child.name,
                             attr=dict(id=node_el_id, rel=child.node_type),
                             children=[],
                             ))
            elif child.level >= 1:
                _data = data[:]
                for depth in range(child.level):
                    _data = _data[-1]['children']
                _data.append(dict(data=child.name,
                                 attr=dict(id=node_el_id, rel=child.node_type),
                                 children=[],
                                 ))
        return data, initially_open

    def render_tree_crud_buttons(self):
        T = current.T
        ui = dict(buttonadd='ui-icon-plusthick',
                  buttondelete='ui-icon-close',
                  buttonedit='ui-icon-pencil')
        return DIV(
            A('x', _class='close', _href='#', _onclick='jQuery(this).parent().hide();'),
            self.recordbutton('%(buttonadd)s' % ui, T('Add'), '#', False, _id='add_node_button'),
            self.recordbutton('%(buttonedit)s' % ui, T('Edit'), '#', False, _id='edit_node_button'),
            self.recordbutton('%(buttondelete)s' % ui, T('Delete'), '#', False, _id='delete_node_button'),
            _id='tree_crud_buttons', _style='display:none;position:absolute;',
            _class='tree_crud_button alert-message info',
        )

    def __call__(self,
                 args=[],
                 user_signature=True,
                 hmac_key=None,
                 onsuccess=None,  # def onsuccess(affected_node_ids): ...
                 ):
        request = current.request

        def url(**b):
            b['args'] = args + b.get('args', [])
            b['user_signature'] = user_signature
            b['hmac_key'] = hmac_key
            return URL(**b)

        def check_authorization():
            if not URL.verify(request, user_signature=user_signature,
                              hmac_key=hmac_key):
                raise HTTP(403)

        action = request.args and request.args[-1]

        if action == 'new':
            check_authorization()
            vars = request.post_vars
            if not vars.name or vars.name == '---':
                raise HTTP(406)
            ''' Agregado IS_SLUG para que no quede en blanco -- Task 33'''
            node_id = self.tree_model.insert_node(vars.target,
                                                  name=vars.name,
                                                  slug=IS_SLUG()(vars.name)[0])

            db_pages.Pages().insert_modules_visibles_all_pages(node_id)

            if onsuccess:
                onsuccess([])
            raise HTTP(200, str(node_id))

        elif action == 'edit':
            check_authorization()
            vars = request.post_vars
            if not vars.name or vars.name == '---':
                raise HTTP(406)
            node = self.tree_model.get_node(vars.id)
            if not node:
                raise HTTP(404)
            if node.name == vars.name:
                raise HTTP(406)
            node.update_record(name=vars.name)
            if onsuccess:
                onsuccess([])
            raise HTTP(200)

        elif action == 'delete':
            check_authorization()
            vars = request.post_vars
            node = self.tree_model.get_node(vars.id)
            #Un leaf_node es un nodo sin hijos, se comprueba que no tenga hijos
            if not self.tree_model.is_leaf_node(node) or not node:
                raise HTTP(404)
            #Se comprueba que no sea una página de sistema # TASK 42
            if db_pages.Pages.Db_Functions().is_system_page(node):
                raise HTTP(404)

            affected_node_ids = [_node.id for _node in self.tree_model.ancestors_from_node(node).select()]

            self.tree_model.delete_node(node)
            if onsuccess:
                onsuccess(affected_node_ids)
            raise HTTP(200)
            
        elif action == 'move':
            check_authorization()
            vars = request.post_vars
            node = self.tree_model.get_node(vars.id)
            if self.tree_model.is_root_node(node):
                raise HTTP(406)
            affected_node_ids = [_node.id for _node in self.tree_model.ancestors_from_node(node).select()]
            
            parent_node = self.tree_model.get_node(vars.parent)
            position = int(vars.position)
            
            target_child = self.tree_model.get_first_child(parent_node)
            if target_child:
                tmp = None
                end_flag = False
                for i in range(position):
                    tmp = self.tree_model.get_next_sibling(target_child)
                    if tmp is False:
                        self.tree_model.move_node(node, target_child, 'right')
                        end_flag = True
                    target_child = tmp
                if end_flag is False:
                    self.tree_model.move_node(node, target_child, 'left')
            else:
                self.tree_model.move_node(node, parent_node)
                
            affected_node_ids += [_node.id for _node in self.tree_model.ancestors_from_node(node).select()]
            if onsuccess:
                onsuccess(list(set(affected_node_ids)))
                
            raise HTTP(200)

        root_nodes = self.tree_model.roots().select()
        data = []
        initially_open = []
        for i, root_node in enumerate(root_nodes):
            _data, _initially_open = self.build_tree_objects(root_node)
            data.append(_data)
            initially_open += _initially_open
        
        from gluon.utils import web2py_uuid
        element_id = web2py_uuid()

        from gluon.globals import Response, Storage
        _response = Response()
        _response._view_environment = current.globalenv.copy()
        _response._view_environment.update(
            request=Storage(folder=os.path.join(os.path.dirname(os.path.dirname(request.folder)), APP)),
            response=_response,
        )
        return XML(_response.render('plugin_jstree/block.html',
                                   dict(url=url, data=data,
                                        initially_open=initially_open,
                                        tree_crud_buttons=self.render_tree_crud_buttons(),
                                        element_id=element_id,
                                        APP=APP)))
