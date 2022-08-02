import os
import json
from django.core.files import File
from io import BytesIO
from unittest.mock import MagicMock
from rest_framework import status
from .setup import APIAuthTestCase, API_ROOT
from ..models import RehagoalUser, Workflow, MAX_FILE_SIZE


class WorkflowAPITestCase(APIAuthTestCase):
    """
    Tests the Workflow API endpoint (/workflows/)
    """

    WORKFLOW_CONTENT_SIMPLE = b'this is a simple text content'
    WORKFLOW_CONTENT_JSON = b'{"name":"mocked file","meta":"nothing"}'
    MAX_FILE_SIZE_EXPECTED = 200 * 1024 * 1024

    @staticmethod
    def api(path="") -> str:
        return API_ROOT + "workflows/" + path

    def assertWorkflowEquals(self, expected_local_workflow: Workflow, actual_remote_workflow: dict):
        expected_fields = {"id", "content", "owner"}
        self.assertSetEqual(expected_fields, set(actual_remote_workflow.keys()))
        self.assertEqual(expected_local_workflow.id, actual_remote_workflow["id"])
        self.assertIn(expected_local_workflow.owner.id, actual_remote_workflow["owner"])
        self.assertRegex(actual_remote_workflow["content"], r'^.*'+API_ROOT+'files/([A-Za-z0-9]{12}|)$')
        self.assertLocalAndRemoteWorkflowContentEqual(expected_local_workflow, actual_remote_workflow)

    @staticmethod
    def getFileSizeExceededResponseJSON():
        return {
            "content": [
                "Invalid file size. The file may not be larger than 200,0\xa0MB. Actual file size was 200,0\xa0MB"
            ]
        }

    def getRemoteWorkflowContent(self, remote_workflow: dict) -> bytes:
        return self.client.get(remote_workflow["content"]).getvalue()

    @staticmethod
    def getLocalWorkflowContent(local_workflow: Workflow) -> bytes:
        with local_workflow.content as content_file:
            content = content_file.read()
            return content

    def assertLocalAndRemoteWorkflowContentEqual(self, db_workflow: Workflow, remote_workflow: dict):
        db_content = self.getLocalWorkflowContent(db_workflow)
        remote_content = self.getRemoteWorkflowContent(remote_workflow)
        self.assertEqual(db_content, remote_content)

    def assertWorkflowContentEqual(self, expected_content: bytes,
                                   actual_remote_workflow: dict, actual_db_workflow: Workflow):
        """
        Asserts that the content of both remote (via GET request) and local (DB) workflows
        are equal to the expected_content.

        Args:
            expected_content (bytes): expected content
            actual_remote_workflow (dict): remote workflow, as returned by APIClient.get on the workflow resource.
            actual_db_workflow (Workflow): workflow retrieved from the database via Django ORM.
        """
        actual_remote_content = self.getRemoteWorkflowContent(actual_remote_workflow)
        actual_db_content = self.getLocalWorkflowContent(actual_db_workflow)
        self.assertEqual(actual_remote_content, expected_content)
        self.assertEqual(actual_db_content, expected_content)

    @staticmethod
    def doesWorkflowFileExist(workflow_name: str) -> bool:
        content_path = os.getcwd() + '/files/%s' % workflow_name
        return os.path.exists(content_path)

    @staticmethod
    def generate_mock_file(content: bytes) -> MagicMock:
        file_mock = MagicMock(spec=File, wraps=BytesIO(content))
        file_mock.name = "mocked_testfile"
        return file_mock

    def setUp(self):
        super(WorkflowAPITestCase, self).setUp()
        Workflow.objects.create(
            owner=RehagoalUser.objects.get(user__username=self.regular_user.username),
            content=self.generate_mock_file(self.WORKFLOW_CONTENT_SIMPLE)
        )
        Workflow.objects.create(
            owner=RehagoalUser.objects.get(user__username=self.regular_user.username),
            content=self.generate_mock_file(b"none")
        )
        Workflow.objects.create(
            owner=RehagoalUser.objects.get(user__username=self.regular_user2.username),
            content=self.generate_mock_file(self.WORKFLOW_CONTENT_JSON)
        )
        self.all_workflows = Workflow.objects.all().order_by("owner")

    def tearDown(self):
        super(WorkflowAPITestCase, self).tearDown()
        Workflow.objects.all().delete()

    def test_list_authentication_required(self):
        """
        Should deny listing for unauthenticated users.
        """

        self.auth()
        r = self.client.get(self.api())
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_head_unauthorized(self):
        """
        Should deny HEAD for unauthenticated users.
        """

        self.auth()
        r = self.client.get(self.api())
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_regular_user(self):
        """
        Should list own workflows for regular users.
        """

        for user in (self.regular_user, self.regular_user2):
            self.auth(user)
            r = self.client.get(self.api())
            user_workflows = Workflow.objects.filter(
                owner__user__username=user.username
            )
            self.assertEqual(len(user_workflows), r.data["count"])
            for expected_workflow, actual_workflow in zip(
                user_workflows, r.data["results"]
            ):
                self.assertWorkflowEquals(expected_workflow, actual_workflow)

    def test_retrieve_head_unauthorized(self):
        """
        Should deny HEAD for unauthorized users.
        """

        self.auth()
        r = self.client.head(self.api("%s/" % self.all_workflows[0].id))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_head_regular_user(self):
        """
        Should allow HEAD for regular users.
        """

        r = self.client.head(self.api("%s/" % self.all_workflows[0].id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_retrieve_unauthorized(self):
        """
        Should deny retrieving a workflow for unauthorized users.
        """

        self.auth()
        for known_workflow in self.all_workflows:
            r = self.client.get(self.api("%s/" % known_workflow.id))
            self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_regular_user(self):
        """
        Should retrieve a workflow for regular users (owner is not relevant).
        """

        for known_workflow in self.all_workflows:
            r = self.client.get(self.api("%s/" % known_workflow.id))
            self.assertEqual(r.status_code, status.HTTP_200_OK)
            self.assertWorkflowEquals(known_workflow, r.data)

    def test_post_unauthorized(self):
        """
        Should deny posting for unauthorized users.
        """

        self.auth()
        new_file = self.generate_mock_file(b"aBcdEE.test")
        r = self.client.post(self.api(), {"content": new_file})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_regular_user(self):
        """
        Should allow posting of new workflows as a regular user.
        """

        self.auth(self.regular_user)
        expected_content = b"aBcdE4.test"
        new_file = self.generate_mock_file(expected_content)
        workflow_json = {"content": new_file}
        r = self.client.post(self.api(), workflow_json)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        db_workflow = Workflow.objects.get(id=r.data["id"])
        self.assertEqual(db_workflow.owner.user.username, self.user.username)
        self.assertWorkflowContentEqual(expected_content, r.data, db_workflow)

    def test_post_regular_user_file_size_exceeded(self):
        """
        Should deny posting of new workflows as a regular user, if MAX_FILE_SIZE is exceeded.
        """

        self.assertEqual(MAX_FILE_SIZE, self.MAX_FILE_SIZE_EXPECTED)
        self.auth(self.regular_user)
        new_file = BytesIO(bytes(MAX_FILE_SIZE + 1))
        data = {"content": new_file}
        r = self.client.post(self.api(), data)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response_content = self.getFileSizeExceededResponseJSON()
        self.assertEqual(json.loads(r.content), expected_response_content)

    def test_post_regular_user_file_size_max(self):
        """
        Should allow posting of new workflows as a regular user, if MAX_FILE_SIZE is not exceeded.
        """

        self.assertEqual(MAX_FILE_SIZE, self.MAX_FILE_SIZE_EXPECTED)
        self.auth(self.regular_user)
        expected_content = bytes(MAX_FILE_SIZE)
        new_file = BytesIO(expected_content)
        data = {"content": new_file}
        r = self.client.post(self.api(), data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        db_workflow = Workflow.objects.get(id=r.data["id"])
        self.assertEqual(db_workflow.owner.user.username, self.user.username)
        self.assertWorkflowContentEqual(expected_content, r.data, db_workflow)

    def test_post_regular_user_unaccepted_fields(self):
        """
        Should allow posting of new workflows as a regular user.
        """

        self.auth(self.regular_user)
        expected_content = b"aBcdEE.test"
        new_file = self.generate_mock_file(expected_content)
        workflow_json = {
            "id": "maliciousId",
            "owner": "badOwner",
            "content": new_file,
        }
        r = self.client.post(self.api(), workflow_json)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        db_workflow = Workflow.objects.get(id=r.data["id"])
        self.assertNotEqual(db_workflow.id, workflow_json["id"])
        self.assertNotEqual(db_workflow.owner.id, workflow_json["owner"])
        self.assertNotEqual(db_workflow.owner.user.username, workflow_json["owner"])
        self.assertEqual(db_workflow.owner.user.username, self.user.username)
        self.assertWorkflowContentEqual(expected_content, r.data, db_workflow)

    def test_delete_regular_user(self):
        """
        Should allow deleting self-owned workflows.
        """

        my_workflows = Workflow.objects.filter(owner=self.rehagoal_user)
        del_workflow = my_workflows[0]
        self.assertTrue(self.doesWorkflowFileExist(del_workflow.content))
        r = self.client.delete(self.api("%s/" % del_workflow.id))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(del_workflow, Workflow.objects.filter(owner=self.rehagoal_user))
        self.assertFalse(self.doesWorkflowFileExist(del_workflow.content), 'Workflow content file should have been deleted')

    def test_delete_not_owned(self):
        """
        Should prevent deleting of workflows owned by other users.
        """

        self.auth(self.regular_user)
        other_workflows = Workflow.objects.all().exclude(owner=self.rehagoal_user)
        del_workflow = other_workflows[0]
        r = self.client.delete(self.api("%s/" % del_workflow.id))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(del_workflow, Workflow.objects.all())

    def test_put_regular_user(self):
        """
        Should allow modification of self-owned workflows.
        """

        my_workflow = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflow[0]
        expected_content = b"aBcdEPUT.test"
        new_file = self.generate_mock_file(expected_content)
        r = self.client.put(
            self.api("%s/" % mod_workflow.id), {"content": new_file}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        new_workflow = Workflow.objects.get(id=mod_workflow.id)
        self.assertWorkflowContentEqual(expected_content, r.data, new_workflow)

    def test_put_regular_user_file_size_max(self):
        """
        Should allow modification, if file size is within limits.
        """
        self.assertEqual(MAX_FILE_SIZE, self.MAX_FILE_SIZE_EXPECTED)
        my_workflow = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflow[0]
        expected_content = bytes(MAX_FILE_SIZE)
        new_file = self.generate_mock_file(expected_content)
        r = self.client.put(
            self.api("%s/" % mod_workflow.id), {"content": new_file}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        new_workflow = Workflow.objects.get(id=mod_workflow.id)
        self.assertWorkflowContentEqual(expected_content, r.data, new_workflow)

    def test_put_regular_user_file_size_exceeded(self):
        """
        Should deny modification of existing workflows as a regular user, if MAX_FILE_SIZE is exceeded.
        """
        self.assertEqual(MAX_FILE_SIZE, self.MAX_FILE_SIZE_EXPECTED)
        my_workflow = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflow[0]
        expected_content = bytes(MAX_FILE_SIZE + 1)
        new_file = BytesIO(expected_content)
        r = self.client.put(
            self.api("%s/" % mod_workflow.id), {"content": new_file}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response_content = self.getFileSizeExceededResponseJSON()
        self.assertEqual(json.loads(r.content), expected_response_content)

    def test_put_incomplete(self):
        """
        Should deny incomplete PUT modification of self-owned workflows.
        """

        my_workflow = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflow[0]
        r = self.client.put(self.api("%s/" % mod_workflow.id), {})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        new_workflow = Workflow.objects.get(id=mod_workflow.id)
        self.assertEqual(mod_workflow, new_workflow)

    def test_patch_regular_user(self):
        """
        Should allow patching of self-owned workflows.
        """

        my_workflow = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflow[0]
        expected_content = b"aBcdEPUT.test"
        new_file = self.generate_mock_file(expected_content)
        r = self.client.patch(
            self.api("%s/" % mod_workflow.id), {"content": new_file}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        new_workflow = Workflow.objects.get(id=mod_workflow.id)
        self.assertWorkflowContentEqual(expected_content, r.data, new_workflow)
        self.assertFalse(self.doesWorkflowFileExist(mod_workflow.content), 'Workflow content file should have been deleted')

    def test_patch_regular_user_file_size_max(self):
        """
        Should allow patching of self-owned workflows, if file size is within limits.
        """
        self.assertEqual(MAX_FILE_SIZE, self.MAX_FILE_SIZE_EXPECTED)
        my_workflow = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflow[0]
        expected_content = bytes(MAX_FILE_SIZE)
        new_file = BytesIO(expected_content)
        r = self.client.patch(
            self.api("%s/" % mod_workflow.id), {"content": new_file}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        new_workflow = Workflow.objects.get(id=mod_workflow.id)
        self.assertWorkflowContentEqual(expected_content, r.data, new_workflow)
        self.assertFalse(self.doesWorkflowFileExist(mod_workflow.content),
                         'Workflow content file should have been deleted')

    def test_patch_regular_user_file_size_exceeded(self):
        """
        Should deny patching of self-owned workflows as a regular user, if MAX_FILE_SIZE is exceeded.
        """
        self.assertEqual(MAX_FILE_SIZE, self.MAX_FILE_SIZE_EXPECTED)
        my_workflow = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflow[0]
        expected_content = bytes(MAX_FILE_SIZE + 1)
        new_file = BytesIO(expected_content)
        r = self.client.patch(
            self.api("%s/" % mod_workflow.id), {"content": new_file}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response_content = self.getFileSizeExceededResponseJSON()
        self.assertEqual(json.loads(r.content), expected_response_content)

    def test_patch_missing_content(self):
        """
        Should keep old content if workflow is updated without a new content.
        """

        my_workflows = Workflow.objects.filter(owner=self.rehagoal_user)
        mod_workflow = my_workflows[0]
        expected_content = self.getLocalWorkflowContent(mod_workflow)
        r = self.client.patch(
            self.api("%s/" % mod_workflow.id), {"id": "abcd"}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        patched_workflow = Workflow.objects.get(id=mod_workflow.id)
        self.assertWorkflowContentEqual(expected_content, r.data, patched_workflow)

    def test_patch_not_owned(self):
        """
        Should deny patching of workflows owned by other users.
        """

        other_workflows = Workflow.objects.all().exclude(owner=self.rehagoal_user)
        mod_workflow = other_workflows[0]
        old_file = mod_workflow.content
        new_file = self.generate_mock_file(b"new content")
        r = self.client.patch(
            self.api("%s/" % mod_workflow.id), {"content": new_file}
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        patched_workflow = Workflow.objects.get(id=mod_workflow.id)
        with patched_workflow.content as content_file:
            with old_file as previous_content:
                self.assertEqual(content_file.read(), previous_content.read())

    def test_get_content_regular_user(self):
        """
        Should GET workflow files for an authenticated user
        """
        self.auth(self.regular_user2)
        for known_workflow in self.all_workflows:
            r = self.client.get(known_workflow.content.url)
            self.assertEqual(r.status_code, status.HTTP_200_OK)
            r.close()

    def test_get_content_unauthorized(self):
        """
        Should deny access to GET workflow files for an un-authenticated user
        """
        self.auth()
        workflow_urls = [API_ROOT + "files/" + "1invalidLink"]
        for known_workflow in self.all_workflows:
            workflow_urls.append(known_workflow.content.url)
        for content_url in workflow_urls:
            r = self.client.get(content_url)
            self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_content_invalid_path(self):
        """
        Should deny workflow files for invalid (length) or unknown links
        """
        self.auth(self.user)
        r = self.client.get(API_ROOT + "files/" + "")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        invalid_urls = [
            "invalid",
            "abcdefghijkl",
            "123456789012",
            "%2e%2e",
            "aaaaBBBB1111",
            "%2e%2e%2fdb%2esqlite3",
            "%2e%2e%2fmanage%2py"
        ]
        for url in invalid_urls:
            r = self.client.get(API_ROOT + "files/" + url)
            self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_content_response_check(self):
        """
        Should validate that file response is Content-Disposition: attachment and Content-type: application/octet-stream
        """
        self.auth(self.regular_user)
        for known_workflow in self.all_workflows:
            r = self.client.get(known_workflow.content.url)
            header_content_type = r.headers['Content-Type']
            header_content_disposition = r.headers['Content-Disposition']
            self.assertEqual(header_content_type, 'application/octet-stream')
            self.assertEqual(header_content_disposition, 'attachment; filename*=UTF-8\'\'%s' % known_workflow.content)
            r.close()
