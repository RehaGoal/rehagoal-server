from rest_framework import status

from .setup import APIAuthTestCase, API_ROOT
from ..models import RehagoalUser


class RehagoalUserAPITestCase(APIAuthTestCase):
    """
    Tests the RehagoalUser API endpoint (/users/)
    """

    @staticmethod
    def api(path=""):
        return API_ROOT + "users/" + path

    def setUp(self):
        super(RehagoalUserAPITestCase, self).setUp()
        self.all_users = RehagoalUser.objects.all().order_by("-user__date_joined")

    def assertUserEqual(self, expected_user, actual_user):
        """
        Checks the actual user (a dict extracted from a response)
        equals the expected RehagoalUser (database object) and has
        all required fields and no more.
        :type expected_user: RehagoalUser
        :param expected_user: expected database user
        :type actual_user: dict
        :param actual_user: actual user (dict extracted from response)
        """

        expected_fields = {"id", "username"}
        self.assertSetEqual(expected_fields, set(actual_user.keys()))
        self.assertEqual(expected_user.id, actual_user["id"])
        self.assertEqual(expected_user.user.username, actual_user["username"])

    def test_list_authentication_required(self):
        """
        Should deny listing for unauthenticated users.
        """

        self.auth()
        r = self.client.get(self.api())
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_deny_regular_user(self):
        """
        Should deny listing for regular users.
        """

        r = self.client.get(self.api())
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_staff_user(self):
        """
        Should allow listing for staff users.
        """

        self.auth(self.staff_user)
        r = self.client.get(self.api())
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.all_users), r.data["count"])
        for expected_user, actual_user in zip(self.all_users, r.data["results"]):
            self.assertUserEqual(expected_user, actual_user)

    def test_options(self):
        """
        Should be readonly for all users.
        """

        self.auth(self.staff_user)
        r = self.client.options(self.api())
        allowed_methods = r["Allow"].split(", ")
        self.assertTrue(
            all(x in ("GET", "HEAD", "OPTIONS") for x in allowed_methods),
            "Unexpected allowed method in: " + str(allowed_methods),
        )

    def test_retrieve_regular_user(self):
        """
        Should retrieve a user for regular users.
        """

        r = self.client.get(self.api("%s/" % self.all_users[0].id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertUserEqual(self.all_users[0], r.data)

    def test_retrieve_head_unauthorized(self):
        """
        Should deny HEAD for unauthorized users.
        """

        self.auth()
        r = self.client.head(self.api("%s/" % self.all_users[0].id))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_regular_user(self):
        """
        Should not allow posting for regular users.
        """

        r = self.client.post(self.api(), {"id": "12345"})
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_staff_user(self):
        """
        Should not allow posting for staff users.
        """

        self.auth(self.staff_user)
        r = self.client.post(self.api(), {"id": "12345"})
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_regular_user(self):
        """
        Should not allow deleting for regular users.
        """

        r = self.client.delete(self.api("%s/" % self.all_users[0].id))
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_staff_user(self):
        """
        Should not allow deleting for staff users.
        """

        self.auth(self.staff_user)
        r = self.client.delete(self.api("%s/" % self.all_users[0].id))
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
