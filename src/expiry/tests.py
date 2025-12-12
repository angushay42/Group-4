import logging
import subprocess
import requests
import time
import os
import dotenv
import datetime

from group4.settings import (
    SCHED_SERVER_PORT, SCHED_SERVER_URL, ENV_PATH
)
from expiry.models import NotifJob

from django.test import TestCase
from django.core import management
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

# Create your tests here.
# https://docs.djangoproject.com/en/5.2/topics/testing/overview/
# https://docs.djangoproject.com/en/5.2/topics/testing/tools/  <-- Client

logger = logging.getLogger("tests")

# environment init
logger.debug(
    f"{__name__} setting up environment..."
)

os.environ.update(dotenv.dotenv_values(ENV_PATH))


class StartupTestCase(TestCase):
    def setUp(self):
        pass
    
    def test_startup_load(self):
        response = self.client.get("/")

        # test OK
        self.assertEqual(response.status_code, 200)


class LoginTestCase(TestCase):
    def setUp(self):
        self.session_timeout = 1209600  # in seconds
        self.test_email ="working@email.com"
        self.test_pass = os.environ['TEST_PASS']

        self.user = User.objects.create_user(
            username=self.test_email,  # feels hacky
            password=self.test_pass
        )

    def test_login_get(self):
        # check that user can access login (GET)
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)

    def test_login_bad_email(self):
        # check if malformed email gets rejected
        # todo add more checks for invalid email, no domain etc
        response = self.client.post("/login", {
            'email': "missing_at_symbol",
            'password': 'testpass'
        })

        self.assertRaises(ValidationError)
        self.assertEqual(response.status_code, 400)

    def test_login_not_authorised(self):
        # check if user is not authorised
        response = self.client.post("/login", {
            'email': "userdoesnotexist@email.com",
            'password': 'testpass'
        })

        self.assertEqual(response.status_code, 401) # unauthorised

    def test_login_authorised(self):
        # todo is authorised user redirected
        response = self.client.post(
            "/login", {
                'email': self.test_email,
                'password': self.test_pass
            }, 
        )

        # useful: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#:~:text=and%20status%20codes.-,If,-you%20had%20a

        # check that user was redirected 
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/dashboard')

    def test_login_remember_me(self):
        # check if session is created
        response = self.client.post(
            "/login", {
                'email': self.test_email,
                'password': self.test_pass,
                'remember_me': "on"
            },
        )

        self.assertTrue(100000 <= self.client.session.get_expiry_age())
        self.assertEqual(response.status_code, 302)


class SchedulerTestCase(TestCase):
    pass


class JobServerTestCase(TestCase):
    BASE_URL = f"http://{SCHED_SERVER_URL}:{SCHED_SERVER_PORT}" # is http needed?

    @classmethod
    def setUpClass(cls):
        logger.debug(
            f"Setting up {cls.__name__}"
        )

        # server and scheduler init
        logger.debug(
            f"Starting apscheduler subprocess..."
        )
        cls.serv_proc = subprocess.Popen(
            ["python3", "manage.py", "runapscheduler", "-t"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        # get api key from environment
        logger.debug(
            f"Getting API key..."
        )
        api_key = os.environ.get("API_KEY")
        if not api_key:
            logger.debug(
                f"ERROR.{__name__}: API ket not found"
            )
            cls.fail(
                cls, 
                "Api key not found"
            )

        # headers used throughout requests
        cls.headers = {
            "Content-type":     "Application/json",
            "Authorization":    f"Bearer {api_key}"
        }

        # User init
        logger.debug(
            f"Creating test user..."
        )
        
        cls.test_email ="working@email.com"
        cls.test_pass = os.environ['TEST_PASS']

        cls.user = User.objects.create_user(
            username=cls.test_email,    # feels hacky
            password=cls.test_pass
        )
        
        # wait for subprocess init
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        logger.debug(
            f"Tearing down {cls.__name__}"
        )
        cls.serv_proc.terminate()
        time.sleep(1)
    
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

        self.assertIsNotNone(notifs)

    def test_add_notification_bad(self):
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

        self.assertEqual(response.json(), {"error": "invalid user"})

        self.assertEqual(response.status_code, 400)     # Bad request 

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


    def test_delete_notification(self):
        logger.debug("{} testing: {}".format(
            self.__class__.__name__,
            "add notification")
        )

        # todo remove this
        self.skipTest("not implemented yet")
        
        test_data = {}
    
        url = self.BASE_URL + '/delete_notification'

        response = requests.post(
            url=url,
            headers=self.headers,
            json=test_data
        )

        self.assertEqual(response.status_code, 200)
        