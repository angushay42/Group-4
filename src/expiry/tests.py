import logging
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .views import login_view, startup

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

    def test_login_rememeber_me(self):
        # todo check if session is created
        response = self.client.post(
            "/login", {
                'email': self.test_email,
                'password': self.test_pass,
                'remember_me': "on"
            },
        )

        self.assertTrue(100000 <= self.client.session.get_expiry_age())
        self.assertEqual(response.status_code, 302)
