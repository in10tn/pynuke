myscheduler = Scheduler(db, dict_tasks)
tasks = db(db.scheduler_task_pynuke.are_sync==False).select()
for t in tasks:
    if db(db.scheduler_task.task_name==t.task_name).count() == 0:
        db.scheduler_task.insert(
                                 application_name=t.application_name,
                                task_name=t.task_name,
                                 group_name=t.group_name,
                                 function_name=t.function_name,
                                 enabled=t.enabled,
                                 start_time=t.start_time,
                                 repeats=t.repeats,
                                 retry_failed=t.retry_failed,
                                 period=t.period,
                                 timeout=t.timeout
                                 )
        db(db.scheduler_task_pynuke.id == t.id).update(are_sync=True)