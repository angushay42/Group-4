import datetime
import logging
import dotenv
import os

from pydantic import BaseModel
from fastapi import Depends, Header, HTTPException
from fastapi.routing import APIRouter
from typing import Annotated
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from group4.settings import ENV_PATH

from expiry.scheduler_inst import get_scheduler


logger = logging.getLogger("jobs")

logger.debug(
    f"{__name__} setting up environment..."
)
os.environ.update(dotenv.dotenv_values(ENV_PATH))

router = APIRouter()
"""
Problem statement:
Ask job server to add a job to be scheduled


how do we know what function is valid?
how do we authenticate?
"""

class PostFunction(BaseModel):
    name: str
    args: list


@router.post('/add_job')
async def add_job( 
    job_function: PostFunction,     # POST request body
):    
    # check that job selected is valid
        # todo how to check function exists within module?
    # check that time requested is valid
    # check that parameters are valid
    # add job 
    
    # what do we do with job_id? 
    return {"message": "job done"}

# idea could use request body if we need something heavier
@router.post('/schedule_notify')
async def schedule_notify(
    user,
    time: datetime.time,
    day_of_week: int,
    scheduler: Annotated[BlockingScheduler, Depends(get_scheduler)]
):
    logger.debug(
        f"/schedule_notify requested"
    )
    cron = CronTrigger(
        year="*",
        month="*", 
        second="{:02d}".format(time.second),
        minute="{:02d}".format(time.minute),
        day_of_week="{}".format(day_of_week)
    )
    job = scheduler.add_job(
        func=some_func, #todo
        trigger=cron,
        args=user,
    )
    # todo might want to return something here?

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