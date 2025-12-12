import logging
import uvicorn
import os
import time
import dotenv
from threading import Thread
from fastapi import (
    FastAPI, Request, HTTPException, Depends, Response
)

from django.conf import settings
from django.utils import timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from expiry.routers import router
from expiry.scheduler_inst import get_scheduler, set_scheduler
from group4.settings import (
    SCHED_SERVER_PORT, SCHED_SERVER_URL,
    ENV_PATH
)

logger = logging.getLogger("jobs")

logger.debug(
    f"{__name__} setting up environment..."
)

os.environ.update(dotenv.dotenv_values(ENV_PATH))

logger.debug(
    f"env path: {ENV_PATH}"
)

# this should be moved to a separate file, too tightly coupled
app = FastAPI()
app.include_router(router=router)

@app.middleware('http')
async def auth_requests(request: Request, call_next):
    logger.debug(
        f"Route: {request.url.path} requested at {timezone.now()}"
    )

    logger.debug(
        f"Route: {request.url.path} getting API key..."
    )

    api_key = os.environ.get('API_KEY')


    if not api_key:
        logger.debug(
            f"ERROR.{__name__}: API key not found"
        )
        # raise TypeError     # todo replace with internal exception

    authorization = request.headers.get('Authorization')
    # authenticate request
    if (not authorization 
        or not authorization.startswith("Bearer ")         # todo hardcoded
        or authorization.split(' ', 1)[1] != api_key
    ):     
        logger.debug(
            f"ERROR: Authorisation header {
                "not found" if not authorization 
                else "invalid"}"
        )
        logger.debug(
            f"auth: {authorization.split(' ', 1)[1]}, key: {api_key}"
        )
        # can't raise exception in middleware. good to know
        return Response(status_code=403)
        
    response = await call_next(request)
    return response



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

    def add_arguments(self, parser):
        parser.add_argument(
            "-t", "--test",         # names
            action="store_true",    # defaults to true if given
        )

    def handle(self, *args, **options):
        # TODO this should be moved to some other file for modularity
        logger.debug(
            f"argument check: {options["test"]}"
        )
        self.test: bool = options["test"]

        # init
        set_scheduler(BlockingScheduler(timezone=settings.TIME_ZONE))
        sched = get_scheduler()
        sched.add_jobstore(DjangoJobStore(), "default")

        # todo from docs, may want to remove? 
        sched.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.debug(
            "Added weekly job: 'delete_old_job_executions'."
        )

        # main
        try:
            logger.debug("Starting scheduler...")

            sched_thread = Thread(
                target=sched.start,
                daemon=True,
            )

            # spin up scheduler
            sched_thread.start()

            # todo disable debug logging, reroute to file instead
            # spin up server (needs to be main thread)
            uvicorn.run(
                app=app,
                host=SCHED_SERVER_URL,
                port=SCHED_SERVER_PORT,
                log_level="debug"
            )
            
        except KeyboardInterrupt:
            logger.debug("Stopping scheduler...")
            sched.shutdown()
            logger.debug("Scheduler shut down successfully!")
