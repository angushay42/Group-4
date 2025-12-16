import logging

from apscheduler.schedulers.blocking import (
    BaseScheduler, BlockingScheduler
)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import SchedulerEvent, EVENT_SCHEDULER_SHUTDOWN
from apscheduler.executors.debug import DebugExecutor
from django_apscheduler.jobstores import DjangoJobStore
from group4 import settings

logger = logging.getLogger('jobs')  # todo make new logger
scheduler = None

# todo remove
def debugger(message: str):
    logger.debug(f"=" * 50)
    logger.debug(message)
    logger.debug(f"=" * 50)

def get_scheduler() -> BaseScheduler:
    global scheduler
    return scheduler

def set_scheduler(sched=None, debug=True):
    # init
    global scheduler
    if not sched:
        debugger(f"making scheduler, args [sched: {sched}, debug: {debug}]")
        scheduler = BackgroundScheduler(
            timezone=settings.TIME_ZONE,
            daemon=True
        )
        if debug:
            scheduler.add_executor(DebugExecutor(), 'debug')

        debugger(f"{scheduler._executors}")
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.add_listener(log_shutdown, EVENT_SCHEDULER_SHUTDOWN)
    else:
        scheduler = sched



def log_shutdown(event: SchedulerEvent):
    debugger(f"scheduler shutting down")
    
