if False:
    from gluon import *    
    request,session,response,T,cache=current.request,current.session,current.response,current.t,current.cache
    from gluon.storage import Storage
    #settings = Storage()
    db = current.db
    MimeMail = current.MimeMail
    import datetime
    from applications.init.modules import db_pynuke, db_eventlog

from gluon.scheduler import Scheduler
clEventLog = db_eventlog.EventLog()

# This table is used by Pynuke to store temporally the tasks created by pynuke
# and the possible modules installed. First, the definition are stored here, 
# and in the last file loaded from models "scheduled_tasksz.py"
# we put these tasks finally in the scheduled_tasks of web2py.
db.define_table(
            'scheduler_task_pynuke',
            Field('application_name', requires=IS_NOT_EMPTY(),
                  default=None, writable=False),
            Field('task_name', default=None, length=255, unique=True),
            Field('group_name', default='main'),
            Field('function_name'),
            Field('enabled', 'boolean', default=True),
            Field('start_time', 'datetime', requires=IS_DATETIME()),
            Field('repeats', 'integer', default=1, comment="0=unlimited",
                  requires=IS_INT_IN_RANGE(0, None)),
            Field('retry_failed', 'integer', default=0, comment="-1=unlimited",
                  requires=IS_INT_IN_RANGE(-1, None)),
            Field('period', 'integer', default=60, comment='seconds',
                  requires=IS_INT_IN_RANGE(0, None)),
            Field('timeout', 'integer', default=60, comment='seconds',
                  requires=IS_INT_IN_RANGE(0, None)),
            Field('are_sync', 'boolean', default=False, comment='When the task are sync it is copied to web2py scheduler',
                  ),
            format='%(task_name)s')


def send_queue():
    try:
        # TODO take in count the param max mails x send_queue in settings
        clEventLog.eventlog("SCHEDULER_STARTED",
                            locals(),
                            [('Event', 'Send Queue')]
                            )
        mail_maximo_num_envios = 1
        orderby = db.messagerecipients.createdon
        query = (db.messagerecipients.emailsent != True)

        if mail_maximo_num_envios > 0:
            limitby = (0, mail_maximo_num_envios)
            rows = db(query).select(orderby=orderby, limitby=limitby)
        else:
            rows = db(query).select(orderby=orderby)

        for row in rows:
            objmessage = db.messages[row.messageid]
            if row.userid != None:
                maildest = db.auth_user[row.userid].email
            else:
                maildest = row.email

            query_attachments = (db.messageattachments.messageid == row.id)
            attachments = db(query_attachments).select()
            lst_attachments = []
            if attachments is not None and len(attachments) > 0:
                for a in attachments:
                    if not a.pathtofile.count("|") > 0:
                        lst_attachments.append(MimeMail.Attachment(a.pathtofile))
                    else:
                        a_decompose = a.pathtofile.split("|")
                        lst_attachments.append(MimeMail.Attachment(a_decompose[1], content_id=a_decompose[2]))

            if MimeMail.send(to=maildest,
                             subject=objmessage.messagesubject,
                             message=(objmessage.messagetxtversion,
                                      objmessage.messagebody
                                      ),
                             attachments=lst_attachments,
                             sender=objmessage.messagefrom,
                             ):
                row.update_record(emailsent=True, emailsentdate=datetime.datetime.now())
            else:
                row.update_record(emailsent=False)
            db.commit()

        clEventLog.eventlog("SCHEDULER_STOPPED", locals(),[('scheduled task:','send_queue'),('Status:','Okay')])
    except:
        clEventLog.eventlog("SCHEDULER_EXCEPTION", locals())
        clEventLog.eventlog("SCHEDULER_STOPPED", locals(),[('Status:','Error')])



def clear_event_log():
    try:
        clEventLog.eventlog("SCHEDULER_STARTED", locals(),[('Event', 'Clean event log')])
        types_in_eventlog = db().select(db.eventlog.typekey, distinct=True)
        clEventLog.eventlog("SCHEDULER_EVENT_PROGRESSING", locals(),[('Distinct Types in eventlog', types_in_eventlog)])
        for tie in types_in_eventlog:
            limit = db.eventlogconfig[tie.typekey].keepmostrecent
            querydeletelog = ''' delete from eventlog where typekey = %s and id not in (select id from eventlog where typekey = %s order by createdate desc limit %s)  ''' % (tie.typekey, tie.typekey, limit)
            clEventLog.eventlog("SCHEDULER_EVENT_PROGRESSING", locals(),[('Query delete log', querydeletelog)])
            db.executesql(querydeletelog)
            db.commit()
            db.executesql("VACUUM")
            db.commit()
            clEventLog.eventlog("SCHEDULER_EVENT_PROGRESSING", locals(),[('VACUUM OK', 'OK')])
        clEventLog.eventlog("SCHEDULER_STOPPED", locals(),[('Event', 'Clean event log')])

    except:
        clEventLog.eventlog("SCHEDULER_EXCEPTION", locals(),[('Event', 'Clean event log')])
        clEventLog.eventlog("SCHEDULER_STOPPED", locals(),[('Event', 'Clean event log')])

#define a dict of tasks here. If more modules are added and these modules are
#need to use more tasks, then we can add items to dictionary with
#    dict_tasks['nametask'] = nametask
#and finally in
#the last file scheduled_tasksz.py we pass the dict to final scheduler object
#and make all tasks available to web2py scheduler

dict_tasks = dict(send_queue=send_queue,
                 clear_event_log=clear_event_log
                                 )

db_pynuke.PyNuke.Scheduler().define_tasks()
