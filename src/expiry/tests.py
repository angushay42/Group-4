import logging
import threading
import subprocess
import requests
import time
import os

from expiry.routers import PostFunction
from group4.settings import SCHED_SERVER_PORT, SCHED_SERVER_URL

from django.test import TestCase
from django.core import management
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

# Create your tests here.
# https://docs.djangoproject.com/en/5.2/topics/testing/overview/
# https://docs.djangoproject.com/en/5.2/topics/testing/tools/  <-- Client

logger = logging.getLogger("tests")

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
        self.test_pass = "sosecret123"

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


"""
I want to test:
- jobs are created
- job server works
    - receives requests
    - handles errors okay
    - has a log file that outputs as expected
- scheduler runs a simple function
- scheduler runs a function with 1 argument
- scheduler runs a function with complex argument (DateTime)
"""

class SchedulerTestCase(TestCase):
    pass

class JobServerTestCase(TestCase):
    BASE_URL = f"http://{SCHED_SERVER_URL}:{SCHED_SERVER_PORT}" # is http needed?

    @classmethod
    def setUpClass(cls):
        logger.debug(
            f"setUp called"
        )
        cls.serv_proc = subprocess.Popen(
            ["python3", "manage.py", "runapscheduler", "-t"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        # can't signal, wrong application for threads
        # cls.serv_thread = threading.Thread(
        #     target=management.call_command,
        #     args=["runapscheduler"],
        #     daemon=True
        # )

        # cls.serv_thread.start()

        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.serv_proc.terminate()
    
    def test_health_check(self):
        logger.debug(
            f"health test called"
        )
        response = requests.get(
            f"{self.BASE_URL}/health"
        )
        self.assertEqual(response.status_code, 200)

    def test_add_job(self):
        logger.debug(
            f"add_job test called"
        )
        headers = {
            "Content-type":     "Application/json",
            "Authorisation":    os.environ["API_KEY"]
        }
        
        test_data = {
            "name": "my_func",
            "args": []
        }

        url = self.BASE_URL + '/add_job'

        response = requests.post(
            url=url,
            headers=headers,
            json=test_data
        )
        self.assertEqual(response.status_code, 200)
        logger.debug(
            f"add_job response: {response.text}"
        )
