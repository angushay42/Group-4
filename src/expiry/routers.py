import datetime
import logging
import dotenv
import os
import cron_converter as cronc

from pydantic import BaseModel
from fastapi import (
    Depends, Header, HTTPException, Response, status
)
from fastapi.routing import APIRouter
from asgiref.sync import sync_to_async
from typing import Annotated
from apscheduler.schedulers.blocking import BaseScheduler
from apscheduler.triggers.cron import CronTrigger

from group4.settings import ENV_PATH
from expiry.models import NotifJob
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


# idea could use request body if we need something heavier
@router.post('/add_notification')
async def add_notification(
    notif: NotificationPackage,
    scheduler: Annotated[
        BaseScheduler, Depends(get_scheduler)
    ],
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
    

    if not notif.days or len(notif.days) > 7:
        logger.debug(
            f"{__name__}.ERROR: invalid day value(s)"
        )
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "invalid days"}

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
        job = sync_to_async(scheduler.add_job)(
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
    
    objs = sync_to_async(NotifJob.objects.bulk_create)(
        [NotifJob(
            user_id=notif.user_id,
            job_id=job
        ) for job in jobs]
    )

    if not objs:
        logger.debug(
            f"{__name__}.ERROR: error creating db jobs"
        )
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "server error"}
    logger.debug(
        f"{__name__}: objects created"
    )

    response.status_code = status.HTTP_201_CREATED
    return {"message": "success"}


@router.get('/health')
async def health(scheduler = Depends(get_scheduler)):
    logger.debug(
        f"/health requested"
    )
    return {
        "message": f"{"in " if scheduler == None else "" }active"
    }


# query database for notification preferences
# params = notif_preferences

# query database using params
# content = database(params)

# convert data to email format
# formatted = convert(email)

# address = user.email
# send_email(user.email, content)