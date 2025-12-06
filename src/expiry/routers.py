from fastapi.routing import APIRouter
from fastapi import Depends
from typing import Annotated
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import datetime

from expiry.scheduler_inst import get_scheduler

# function to send notification

router = APIRouter()

# idea could use request body if we need something heavier
@router.post('/schedule_notify')
async def schedule_notify(
    user,
    time: datetime.time,
    day_of_week: int,
    scheduler: Annotated[BlockingScheduler, Depends(get_scheduler)]
):
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
    return {
        "message": f"scheduler is {"not " if scheduler == None else "" }active"
    }


# query database for notification preferences
# params = notif_preferences

# query database using params
# content = database(params)

# convert data to email format
# formatted = convert(email)

# address = user.email
# send_email(user.email, content)