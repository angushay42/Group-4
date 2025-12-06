from apscheduler.schedulers.blocking import BaseScheduler

scheduler = None

def get_scheduler() -> BaseScheduler:
    return scheduler

def set_scheduler(sched):
    global scheduler
    scheduler = sched