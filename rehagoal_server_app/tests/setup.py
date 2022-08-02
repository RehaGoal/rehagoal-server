import base64
from collections import namedtuple

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.crypto import get_random_string
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.test import APIClient

from ..models import SimpleUser


Credentials = namedtuple("Credentials", ["username", "password"])
API_ROOT = "/api/v2/"


class UserTestCase(TestCase):
    def test_user_creates_rehagoal_user(self):
        user = User.objects.create_user("testuser", password="testpass")
        user.is_superuser = False
        user.is_staff = False
        user.save()
        self.assertIsNotNone(User.objects.get(username="testuser").rehagoal_user)

    def test_simpleuser_creates_rehagoal_user(self):
        user = SimpleUser.objects.create_user("testuser", password="testpass")
        user.is_superuser = False
        user.is_staff = False
        user.save()
        self.assertIsNotNone(SimpleUser.objects.get(username="testuser").rehagoal_user)


class APIAuthTestCase(TestCase):
    """
    TestCase base class which already has an APIClient (self.client),
    creates users for testing, and allows authorization self.
    """

    def auth(self, user=None):
        """
        Store credentials for authentication with the server.
        :type user: Credentials | None
        :param user: User to use for HTTP basic authentication
        """

        if not user:
            self.client.credentials()
        else:
            self.client.credentials(
                HTTP_AUTHORIZATION="Basic "
                + base64.b64encode(
                    ("%s:%s" % (user.username, user.password)).encode(
                        HTTP_HEADER_ENCODING
                    )
                ).decode(HTTP_HEADER_ENCODING)
            )
            self.rehagoal_user = User.objects.get(username=user.username).rehagoal_user
        self.user = user

    def setUp(self):
        """
        Initializes an APIClient, creates regular users and a staff user,
        authenticates as regular user.
        """

        self.client = APIClient()
        self.regular_user = Credentials(username="testuser", password="testpassword")
        self.regular_user2 = Credentials(username="testuser2", password="testpassword2")
        self.staff_user = Credentials(username="admin", password=get_random_string(20))

        User.objects.create_user(
            username=self.regular_user.username,
            email="testuser@localhost",
            password=self.regular_user.password,
        )
        User.objects.create_user(
            username=self.regular_user2.username,
            email="testuser2@localhost",
            password=self.regular_user2.password,
        )
        User.objects.create_user(
            username=self.staff_user.username,
            email="admin@localhost",
            password=self.staff_user.password,
            is_staff=True,
        )

        self.auth(self.regular_user)
