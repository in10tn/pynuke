#!/usr/bin/env python
# encoding: utf-8

from gluon import *
#import datetime

class WorkFlows(object):
	
	def __init__(self):
		from gluon.globals import current
		self.db = current.db
		self.T = current.T
		self.auth = current.auth

	def define_tables(self):
		T = self.T
		db = self.db
		
		db.define_table('workflow',
            Field('workflowname','string',length=100),
            Field('description','text'),
            Field('isdeleted','boolean'),            
            format='%(workflowname)s',
            plural='workflow',
            singular = 'workflows',   
            )		
		
		db.define_table('workflowstates',
            Field('workflowid',db.workflow),
            Field('statename','text'),
            Field('ordering','integer'),
            Field('isactive','boolean'),
            Field('notify','boolean'),
            format='%(statename)s',
            plural='workflowstates',
            singular = 'workflowstate',   
            )	
	
#		db.commit()
		
		return;
		
	def insert_initial_records(self):
		T = self.T
		db = self.db

		dp_id = db.workflow.insert(workflowname='Direct Publish')
		dp_cs = db.workflow.insert(workflowname='Content Staging')
		
		db.workflowstates.insert(workflowid =dp_id ,statename='Published',ordering=1,isactive=True,notify=False)
		
		
		
		
		db.commit()
		
		return;
