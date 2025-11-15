from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .views import login_view, startup
import logging

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
                'email': "working@email.com",
                'password': 'testpass'
            }, 
            follow=True
        )

        # useful: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#:~:text=and%20status%20codes.-,If,-you%20had%20a

        logger.debug(response.redirect_chain)

        # check that user was redirected 
        self.assertEqual(len(response.redirect_chain), 1)

        # check that redirect is correct
        self.assertEqual(
            response.redirect_chain[0][0], 
            'http://127.0.0.1/dashboard'    # in tuple form (url, code)
        )
        
        self.assertEqual(response.status_code, 302) # status code 3XX ?? 302?

    def test_login_rememeber_me(self):
        # todo check if session is created
        response = self.client.post(
            "/login", {
                'email': "working@email.com",
                'password': 'testpass',
                'remember_me': True
            },
            follow=True
        )

        self.assertEqual(len(response.redirect_chain), 1)

        self.assertEqual(
            response.redirect_chain[0][0],  # in tuple form (url, code)
            'http://127.0.0.1/dashboard'    
        )

        self.assertEqual(
            self.client.session.get_expiry_age(), 
            self.session_timeout,
        )
        self.assertEqual(response.status_code, 302)

    def test_login_not_rememeber_me(self):
        # check if remember_me = False, session is 0
        response = self.client.post(
            "/login", {
                'email': "working@email.com",
                'password': 'testpass',
                'remember_me': False  # just making sure it's False
            },
            follow=True
        )

        self.assertEqual(len(response.redirect_chain), 1)

        self.assertEqual(
            response.redirect_chain[0][0],  # in tuple form (url, code)
            'http://127.0.0.1/dashboard'    
        )

        self.assertEqual(
            self.client.session.get_expiry_age(), 
            0,
        )

        self.assertEqual(response.status_code, 200)