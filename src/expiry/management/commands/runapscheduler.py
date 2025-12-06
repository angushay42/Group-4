import logging
import uvicorn
from threading import Thread
from fastapi import FastAPI

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from expiry.routers import router
from expiry.scheduler_inst import get_scheduler, set_scheduler
from group4.settings import SCHED_SERVER_PORT, SCHED_SERVER_URL

#todo
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(router=router)

# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way. 
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.
    
    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        # init
        set_scheduler(BlockingScheduler(timezone=settings.TIME_ZONE))
        sched = get_scheduler()
        sched.add_jobstore(DjangoJobStore(), "default")

        # from docs, may want to remove? 
        sched.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        # main
        try:
            logger.info("Starting scheduler...")

            sched_thread = Thread(
                target=sched.start,
                daemon=True,
            )

            # spin up scheduler
            sched_thread.start()

            # spin up server (needs to be main thread)
            uvicorn.run(
                app=app,
                host=SCHED_SERVER_URL,
                port=SCHED_SERVER_PORT
            )
            
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            sched.shutdown()
            logger.info("Scheduler shut down successfully!")
