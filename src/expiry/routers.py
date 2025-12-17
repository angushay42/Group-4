import datetime
import logging
import dotenv
import os


from typing import Annotated
from pydantic import BaseModel
from fastapi import (
    Depends, Header, HTTPException, Response, status
)
from fastapi.routing import APIRouter
from asgiref.sync import sync_to_async
from apscheduler.schedulers.blocking import BaseScheduler
from apscheduler.triggers.cron import CronTrigger

from group4 import settings
from django.db import connection
from group4.settings import ENV_PATH
from expiry.models import NotifJob, User
from expiry.notifications import send_notification
from expiry.scheduler_inst import get_scheduler

logger = logging.getLogger("jobs")

logger.debug(
    f"{__name__} setting up environment..."
)
os.environ.update(dotenv.dotenv_values(ENV_PATH))

router = APIRouter()

class NotificationPackage(BaseModel):
    user_id: int
    days: list[int]
    time: dict[str, int]

class JobPackage(BaseModel):
    user_id: int | None = None
    job_id: str | None = None

# ------------------ Utilities ------------------
def debugger(message: str):
    logger.debug(f"=" * 50)
    logger.debug(message)
    logger.debug(f"=" * 50)

def dummy_job():
    logger.debug(f"Dummy job fired")


# ------------------ Routes ---------------------
@router.post('/add_notification')
async def add_notification(
    notif: NotificationPackage,
    scheduler: Annotated[BaseScheduler, Depends(get_scheduler)],
    response: Response    
):
    logger.debug(
        f"{__name__}: /add_notification requested"
    )

    logger.debug(
        f"{__name__} getting time"
    )
    notif_minute = notif.time.get('minute')
    notif_hour = notif.time.get('hour')

    try:
        notif_time = datetime.time(
            hour=notif_hour,    
            minute=notif_minute
        )
        logger.debug(
            f"{__name__}: time creation success"
        )
    except (ValueError, TypeError) as e:
        logger.debug(
            f"{__name__}.ERROR: invalid time values"
        )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "invalid time"}
    

    if (not notif.days
        or len(notif.days) > 7 
        or not (
            min(notif.days) >= 0 
            and max(notif.days) < 7)
        ):
        logger.debug(
            f"{__name__}.ERROR: invalid day value(s)"
        )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "invalid day"}

    try:
        user = await sync_to_async(User.objects.get)(id=notif.user_id)
    except User.DoesNotExist:
        logger.debug(
            f"ERROR: Invalid username"
        )
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "invalid user"}


    jobs = []
    logger.debug(
        f"{__name__}: creating job(s)"
    )
    #bug
    # potentially dangerous, make sure list size is limited and validated
    for day in notif.days:
        
        cron = CronTrigger(
            year="*",
            month="*", 
            second="00",
            minute="{:02d}".format(notif_time.minute),
            hour="{0:2d}".format(notif_time.hour),
            day_of_week="{}".format(day)
        )
        job = await sync_to_async(scheduler.add_job)(
            func=send_notification,
            trigger=cron,
            args=[notif.user_id],   # needed to be list
        )
        jobs.append(job)
    
    if len(jobs) != len(notif.days):
        logger.debug(
            f"{__name__}.ERROR: error creating jobs"
        )
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "server error"}

    logger.debug(
        f"{__name__}: jobs created"
    )
    
    objs = await sync_to_async(NotifJob.objects.bulk_create)(
        [NotifJob(
            user_id=notif.user_id,
            job_id=job.id   # string
        ) for job in jobs]
    )

    if not objs:
        logger.debug(
            f"{__name__}.ERROR: error creating db jobs"
        )
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "server error"}
    
    logger.debug(
        f"{__name__}: objects created: {objs}"
    )

    response.status_code = status.HTTP_201_CREATED
    return {"message": "success"}


# todo also needs to delete from scheduler no? 
@router.post('/delete_notification')
async def delete_notification(
    body: JobPackage,
    response: Response,
    scheduler: Annotated[BaseScheduler, Depends(get_scheduler)],
):
    logger.debug(
        f"delete_notification called"
    )

    if (body.job_id is None) == (body.user_id is None):
        logger.debug(
            f"no arguments given. body:{body.job_id}, user:{body.user_id}"
        )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "no arguments"}
    
    if body.job_id:
        try: 
            logger.debug(
                f"trying job_id {body.job_id}..."
            )

            # todo remove this
            all_ = await sync_to_async(NotifJob.objects.all)()
            all_ = await sync_to_async(list)(all_)
            logger.debug(
                f"all job objects{all_}"
            )
            # should be unique
            job = await sync_to_async(NotifJob.objects.get)(
                job_id=body.job_id
            )
            logger.debug(
                f"job_id returned job {job}. body: {body.job_id}, job: {job.job_id}"
            )
            # delete job
            await sync_to_async(scheduler.remove_job)(job.job_id)
            await sync_to_async(job.delete)()
            logger.debug(
                f"job deleted"
            )
            
        except NotifJob.DoesNotExist:
            logger.debug(
                f"invalid job id: {body.job_id}"
            )
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid job"}
        
    else:   # user_id
        try: 
            logger.debug(
                f"trying user_id..."
            )
            jobs = await sync_to_async(NotifJob.objects.filter)(
                user__id=body.user_id   # FK lookup
            )
            jobs = await sync_to_async(list)(jobs)
            logger.debug(
                f"user_id returned jobs: {jobs}"
            )
            if not jobs:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {"error": "invalid user_id"}

            # go through jobs and delete
            for job in jobs:
                await sync_to_async(scheduler.remove_job)(job.job_id)
                await sync_to_async(job.delete)()
            logger.debug(
                f"user jobs deleted"
            )
            
        except NotifJob.DoesNotExist:
            logger.debug(
                f"invalid user id: {body.user_id}"
            )
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "invalid user"}
        
    # todo scheduler needs to delete job entry also

    return {"message": "deletion succcessful"}


@router.get('/health')
async def health(
    scheduler = Depends(get_scheduler)
):
    logger.debug(
        f"/health requested"
    )
    # todo more info if needed
    logger.debug(
        ""
    )
    return {"status": "active"}

# ------------------ Testing Routes -------------

async def _add_job(
    job_id: str, 
    response: Response,
    scheduler: Annotated[BaseScheduler, Depends(get_scheduler)]
):
    """Add a job directly to scheduler. FOR TESTING ONLY. """
    logger.debug(f"testing _add_job test method")
    jobs = await sync_to_async(scheduler.get_jobs)()
    if any([job.id == job_id for job in jobs]):
        logger.debug(
            f"invalid job id: {job_id}"
        )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "job already exists"}

    await sync_to_async (scheduler.add_job)(
        dummy_job, 
        trigger=CronTrigger(day=20),
        id=job_id
    )
    response.status_code = 200  # success
    return {"message": "job added successfully"}

async def _del_job(
    job_id: str, 
    response: Response,
    scheduler: Annotated[BaseScheduler, Depends(get_scheduler)]
):
    """Delete a job directly from scheduler. FOR TESTING ONLY. """
    logger.debug(f"testing _del_job test method")
    jobs = await sync_to_async(scheduler.get_jobs)()
    if not any([job.id == job_id for job in jobs]):     # not any == none
        logger.debug(
            f"invalid job id: {job_id}"
        )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "job does not exist"}

    await sync_to_async (scheduler.remove_job)(job_id=job_id)

    response.status_code = 200  # created
    return {"message": "job deleted successfully"}


async def _clear_jobs(
    response: Response,
    scheduler: Annotated[BaseScheduler, Depends(get_scheduler)]
):
    """Delete ALL jobs from scheduler. FOR TESTING ONLY. """
    logger.debug(f"deleting all jobs from scheduler...")
    try:
        await sync_to_async(scheduler.remove_all_jobs)()
    except TypeError as e:
        logger.debug(f"CRITICAL ERROR: could not delete all jobs: {e}")
        response.status_code = 400
    response.status_code = 200
    return {'message': 'deleted all jobs successfully'}


# ------------------ Adding routes --------------
if os.environ.get('TESTING') == "1":
    # todo add more
    router.add_api_route(
        '/_add_job', 
        _add_job,
        methods=['POST'],
        dependencies=[Depends(get_scheduler)]
    )
    router.add_api_route(
        '/_del_job', 
        _del_job,
        methods=['POST'],
        dependencies=[Depends(get_scheduler)]
    )
    router.add_api_route(
        '/_clear_jobs', 
        _clear_jobs,
        methods=['POST'],
        dependencies=[Depends(get_scheduler)]
    )
