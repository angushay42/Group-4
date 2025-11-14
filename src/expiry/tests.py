from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User

from .views import login_view, startup

# Create your tests here.
# https://docs.djangoproject.com/en/5.2/topics/testing/overview/
# https://docs.djangoproject.com/en/5.2/topics/testing/tools/  <-- Client

class StartupTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # create user for sessions
        self.user = User.objects.create_user(
            username='test@gmail.com', password='blank'
        )
    
    def test_startup_load(self):
        request = self.factory.get("/")
        response = startup(request)

        # test OK
        self.assertEqual(response.status_code, 200)


class LoginTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.test_emails = [
           "goodemail@example.com",
           "incomplete",
        ]

    def test_login_get(self):
        request = self.factory.get("/login")

        response = login_view(request)
        self.assertEqual(response.status_code, 200)

    def test_login_get(self):
        request = self.factory.post("/login", {
            'email': self.test_emails[0],
            'password': 'testpass'
        })

        # todo check if malformed input gets rejected
        # should this be clientside?

        response = login_view(request)
        self.assertEqual(response.status_code, 200)

        # todo check if user has been created


       

    pass