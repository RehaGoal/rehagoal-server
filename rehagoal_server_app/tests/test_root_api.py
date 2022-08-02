from rest_framework import status

from .setup import APIAuthTestCase, API_ROOT


class RootAPITestCase(APIAuthTestCase):
    """
    Tests the API root (/)
    """

    @staticmethod
    def api(path=""):
        return API_ROOT + path

    def test_authentication_required(self):
        """
        Should deny access for unauthenticated users.
        """

        self.auth()
        response = self.client.get(self.api())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_head_unauthorized(self):
        """
        Should deny HEAD for unauthenticated users.
        """

        self.auth()
        response = self.client.head(self.api())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_endpoints_regular_user(self):
        """
        Should deny listing of API endpoints for regular users.
        """

        response = self.client.get(self.api())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_endpoints_staff_user(self):
        """
        Should allow API endpoint listing for staff users.
        """

        self.auth(self.staff_user)
        response = self.client.get(self.api())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertSetEqual(set(response.data.keys()), {"workflows", "users"})

    def test_v1_endpoint_gone(self):
        """
        Should respond with 410 GONE for old v1 API endpoint for regular users.
        """

        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
