import json
import os
import logging
import subprocess
import threading
import requests
import time
import os
import dotenv
import datetime

from group4.settings import (
    SCHED_SERVER_PORT, SCHED_SERVER_URL, ENV_PATH, TIME_ZONE
)
from expiry.scheduler_inst import get_scheduler, set_scheduler
from expiry.models import NotifJob

from apscheduler.events import (
    EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
)
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User

# Create your tests here.
# https://docs.djangoproject.com/en/5.2/topics/testing/overview/
# https://docs.djangoproject.com/en/5.2/topics/testing/tools/  <-- Client

logger = logging.getLogger("tests")


test_executed = False

# todo remove
def debugger(message: str):
    logger.debug(f"=" * 50)
    logger.debug(message)
    logger.debug(f"=" * 50)

# environment init
debugger(f"{__name__} setting up environment...")
os.environ.update(dotenv.dotenv_values(ENV_PATH))


class StartupTestCase(TestCase):
    def setUp(self):
        pass
    
    def test_startup_load(self):
        response = self.client.get("/")

        # test OK
        self.assertEqual(response.status_code, 200)


class LoginTestCase(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        cls.session_timeout = 1209600  # in seconds
        cls.test_name = "test"
        cls.test_email ="working@email.com"
        cls.test_pass = os.environ.get('TEST_PASS')

        cls.headers = {
            'Authorization': f"Bearer {os.environ.get('API_KEY')}"
        }

    @classmethod
    def tearDownClass(cls):
        # todo delete user
        try:
            user = User.objects.get(username=cls.test_name)
            logger.debug(f"Deleting user: {cls.test_name}")
            user.delete()
        except User.DoesNotExist:
            logger.debug(f"User does not exist {cls.test_name}")
    
    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user(
            username=self.test_name,
            email=self.test_email,
            password=self.test_pass
        )
        self.client = Client()
        try:
            count = User.objects.filter(username=self.test_name).count()
            logger.debug(f"user count AFTER setUp: {count}")
        except User.DoesNotExist:
            logger.debug(f"user does not exist")
        
    def tearDown(self):
        try:
            count = User.objects.filter(username=self.test_name).count()
            logger.debug(f"user count BEFORE teardown: {count}")
        except User.DoesNotExist:
            logger.debug(f"user does not exist")
        super().tearDown()
        try:
            count = User.objects.filter(username=self.test_name).count()
            logger.debug(f"user count AFTER teardown: {count}")
        except User.DoesNotExist:
            logger.debug(f"user does not exist")

    def test_login_get(self):
        # check that user can access login (GET)
        debugger(f"checking login_get")

        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)

    def test_login_not_authorised(self):
        # check if user is not authorised
        debugger(f"checking login_not_authorised")

        response = self.client.post(
            "/login", {
                'username': 'notfound',
                'email': "userdoesnotexist@email.com",
                'password': 'testpass',
                'test_name': "test_login_not_authorised"
            },
            headers=self.headers
        )

        self.assertEqual(response.status_code, 401)     # unauthorised

    def test_login_authorised(self):
        # todo is authorised user redirected

        debugger(f"checking login_authorised")

        response = self.client.post(
            "/login", {
                'username': self.test_name,
                'email': self.test_email,
                'password': self.test_pass,
                'test_name': "test_login_authorised"
            }, 
            headers=self.headers
        )

        # useful: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#:~:text=and%20status%20codes.-,If,-you%20had%20a

        # check that user was redirected 
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/dashboard')

    def test_login_remember_me(self):
        # check if session is created
        debugger(f"checking login_remember_me")

        response = self.client.post(
            "/login", {
                'username': self.test_name,
                'email': self.test_email,
                'password': self.test_pass,
                'remember_me': "on",
                'test_name': "test_login_rememeber_me"
                
            },
            headers=self.headers
        )

        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.content}")

        self.assertTrue(100000 <= self.client.session.get_expiry_age())
        self.assertEqual(response.status_code, 302)


def dummy_test_public():
    global test_executed
    test_executed = True

class SchedulerTestCase(TransactionTestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        debugger(f"setting up {cls.__name__}")

        cls.timeout = 5     # seconds
        cls.executed = False
        cls.job_events = []

        cls.scheduler = set_scheduler(debug=True)
        cls.scheduler = get_scheduler()

        # Add event listeners to track what's happening
        cls.scheduler.add_listener(cls.job_executed_listener, EVENT_JOB_EXECUTED)
        cls.scheduler.add_listener(cls.job_error_listener, EVENT_JOB_ERROR)
        cls.scheduler.add_listener(cls.job_missed_listener, EVENT_JOB_MISSED)
        
        print(f"Executors: {cls.scheduler._executors}")
        print(f"Jobstores: {cls.scheduler._jobstores}")
        
        cls.scheduler.start()
        
        print(f"Scheduler running: {cls.scheduler.running}")
        print(f"Scheduler state: {cls.scheduler.state}")
        
    @classmethod
    def job_executed_listener(cls, event):
        print(f"!!! JOB EXECUTED EVENT: {event}")
        cls.job_events.append(('executed', event))
        
    @classmethod
    def job_error_listener(cls, event):
        print(f"!!! JOB ERROR EVENT: {event}")
        print(f"!!! Exception: {event.exception}")
        print(f"!!! Traceback: {event.traceback}")
        cls.job_events.append(('error', event))
        
    @classmethod
    def job_missed_listener(cls, event):
        print(f"!!! JOB MISSED EVENT: {event}")
        cls.job_events.append(('missed', event))
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        bef = time.time()
        cls.scheduler.shutdown()
        debugger(f"scheduler took {time.time() - bef:3f} seconds to shutdown.")

        # should be fine
   
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.executed = False
        
    @staticmethod
    def dummy_job():
        global test_executed
        test_executed = True
        with open('test.txt', 'a') as f:    
            print(f"dummy job executing at {time.time()}", file=f)


    def _add_job(self):
        delta = (
            datetime.datetime.now() 
            + datetime.timedelta(seconds=self.timeout)
        )

        trig = CronTrigger(
            hour=delta.hour,
            minute=delta.minute,
            second=delta.second,
            timezone=TIME_ZONE
        )
        job = self.scheduler.add_job(
            dummy_test_public,
            trigger=trig,
        )
        return job

    def test_add_job(self):
        job = self._add_job()

        self.assertIsNotNone(job)
        self.assertIsNotNone(self.scheduler.get_jobs())

    def test_job_exec(self):
        # make a trigger that is soon
        # add a job 
        
        job = self._add_job()
        time.sleep(self.timeout + 1)

        debugger(f"{job.executor}")

        global test_executed
        self.assertTrue(test_executed)

    
class JobServerTestCase(TransactionTestCase):
    BASE_URL = f"http://{SCHED_SERVER_URL}:{SCHED_SERVER_PORT}" # is http needed?

    @classmethod
    def setUpClass(cls):
        logger.debug(f"Setting up {cls.__name__}")

        # get api key from environment
        logger.debug(f"Getting API key...")
        
        api_key = os.environ.get("API_KEY")
        if not api_key:
            logger.debug(f"ERROR.{__name__}: API ket not found")
            cls.fail(cls, "Api key not found")

        cls.test_email ="working@email.com"
        cls.test_pass = os.environ['TEST_PASS']


        # server and scheduler init
        logger.debug(
            f"Starting apscheduler subprocess..."
        )

        env = os.environ.copy()

        # todo dunno if still needed..? 
        # call_command('makemigrations')
        # call_command('migrate', verbosity=1, interactive=False)

        # with open('tests.txt', "a") as f:
        #     # todo
        #     print("="*50, file=f)
        #     print(f"environment created", file=f)
        #     print("="*50, file=f)

        cls.serv_proc = subprocess.Popen(
            ["python3", "manage.py", "runapscheduler", "-t"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=env
        )

        # headers used throughout requests
        cls.headers = {
            "Content-type":     "Application/json",
            "Authorization":    f"Bearer {api_key}"
        }
        
        # wait for subprocess init
        time.sleep(1)

        super().setUpClass()    # todo needed?

    @classmethod
    def tearDownClass(cls):
        logger.debug(
            f"Tearing down {cls.__name__}"
        )

        # todo send a signal to tell the process to stop 
        # so that the scheduler doesn't f up
        cls.serv_proc.terminate()
        time.sleep(0.2)

    def setUp(self):
        super().setUp()
        logger.debug(
            "setting up each test job"
        )

        self.user = User.objects.create_user(
            username=self.test_email,
            password=self.test_pass
        )
        logger.debug(f"test user created: {self.user.pk}")

        self.test_job_id = "420"
        self.test_job = NotifJob.objects.create(
            user=self.user,
            job_id=self.test_job_id
        )

        logger.debug(
            f"test job created: {self.test_job.job_id}"
        )
    
    def tearDown(self):
        super().tearDown()
        logger.debug(f"tearing down each test job")

        try:
            user = User.objects.get(id=self.user.pk)
            user.delete()
            
        except User.DoesNotExist:
            logger.debug(f"user does not exist")

        if NotifJob.objects.filter(job_id=self.test_job_id).exists():
            logger.debug(f"deleting test job")
            self.test_job.delete()
    
    def test_health_check(self):
        logger.debug(
            f"health test called"
        )
        response = requests.get(
            f"{self.BASE_URL}/health",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['status'], "active"
        )
    
    def test_health_check_environ(self):
        response = requests.get(
            f"{self.BASE_URL}/health",
            headers=self.headers
        )

    def test_handling(self):
        """Test the server's error handling

        unauthorised access
        """
        logger.debug(
            f"{__class__.__name__} handling test called"
        )

        response = requests.get(
            f"{self.BASE_URL}/health",
            headers={'Authorization': 'Bearer madeuptoken'}
        )

        self.assertEqual(response.status_code, 403)

    def test_add_notification_good(self):
        logger.debug(
            "{} testing: {}".format(
                self.__class__.__name__,
                "add notification"
            )
        )
        url = self.BASE_URL + '/add_notification'
        
        # good data
        days = [0, 1]   # Mon, Tue
        notif_time = datetime.time(13, 49)

        test_data = {
            "user_id": self.user.pk,
            "days": days,
            "time": {
                "hour": notif_time.hour,
                "minute": notif_time.minute
            }
        }
    
        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        self.assertEqual(response.status_code, 201) # Created

        # check changes have persisted
        notifs = NotifJob.objects.filter(
            user__id=self.user.pk,
        )
        logger.debug(
            f"notifs persistence check: {notifs.first().job_id}"
        )

        self.assertIsNotNone(notifs)

    def test_add_notification_bad_user(self):
        logger.debug(
            "{} testing: {}".format(
                self.__class__.__name__,
                "add notification"
            )
        )
        url = self.BASE_URL + '/add_notification'
        
        days = [0]  # Mon
        notif_time = datetime.time(13, 49)

        test_data = {
            "user_id": 43,  # invalid user, not created in test DB
            "days": days,
            "time": {
                "hour": notif_time.hour,
                "minute": notif_time.minute
            }
        }
    
        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )
        logger.debug(
            f"response: {response.text}"
        )
        message = response.json()
        self.assertIsNotNone(message)
        self.assertTrue(type(message) == dict)
        self.assertEqual(response.json(), {"error": "invalid user"})

        self.assertEqual(response.status_code, 401) # unauthorised

    def test_add_notification_bad_day(self):
        logger.debug(
            "{} testing: {}".format(
                self.__class__.__name__,
                "add notification"
            )
        )
        url = self.BASE_URL + '/add_notification'

        # bad data
        days = [40]     # invalid day 
        notif_time = datetime.time(13, 49)

        test_data = {
            "user_id": self.user.pk,
            "days": days,
            "time": {
                "hour": notif_time.hour,
                "minute": notif_time.minute
            }
        }

        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        self.assertEqual(response.json(), {"error": "invalid day"})

        self.assertEqual(response.status_code, 400)     # Bad request 

    def test_add_notification_bad_time(self):
        logger.debug(
            "{} testing: {}".format(
                self.__class__.__name__,
                "add notification"
            )
        )
        url = self.BASE_URL + '/add_notification'


        days = [0]
        test_data = {
            "user_id": self.user.pk,
            "days": days,
            "time": {
                "hour": 10000,  # bad data
                "minute": -1    # bad data
            }
        }

        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        self.assertEqual(response.json(), {"error": "invalid time"})

        self.assertEqual(response.status_code, 400)     # Bad request 

    def test_delete_notification_no_params(self):
        logger.debug("{} testing: {}".format(
            self.__class__.__name__,
            "delete notification")
        )
        
        # delete ALL notification jobs associated with user
        test_data = {}
    
        url = self.BASE_URL + '/delete_notification'

        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "no arguments"})

    def test_delete_notification_user(self):
        logger.debug("{} testing: {}".format(
            self.__class__.__name__,
            "delete notification")
        )

        # delete ALL notification jobs associated with user
        test_data = {
            "user_id": self.user.pk,
        }
    
        url = self.BASE_URL + '/delete_notification'

        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        logger.debug(
            f"user test response: {response.text}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "deletion succcessful"})

    def test_delete_notification_job(self):
        logger.debug("{} testing: {}".format(
            self.__class__.__name__,
            "delete notification")
        )

        # delete specific notification job
        test_data = {
            "job_id": self.test_job_id
        }

        url = self.BASE_URL + '/delete_notification'

        logger.debug(
            f"jobs: {NotifJob.objects.all()}"
        )

        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        logger.debug(
            f"job test response: {response.text}"
        )

        # todo check job was deleted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "deletion succcessful"})
    
    def test_delete_notification_bad_user(self):
        logger.debug("{} testing: {}".format(
            self.__class__.__name__,
            "delete notification")
        )
        #todo could be more thorough, i.e. typing

        # delete specific notification job
        test_data = {
            "job_id": "10000"
        }
    
        url = self.BASE_URL + '/delete_notification'

        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        logger.debug(
            f"response: {response.text}"
        )
        try:
            message = response.json()
            debugger(f"bad user response json: {json.dumps(message, indent=2)}")
        except json.JSONDecodeError:
            logger.debug(f"couldn't read response")

        self.assertEqual(response.status_code, 400) # bad request
        
        