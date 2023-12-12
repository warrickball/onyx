from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, generate_test_data, _test_record
from ...models.projects.test import TestModel


# TODO: Tests for update endpoint
class TestUpdateView(OnyxTestCase):
    def setUp(self):
        """
        Create a user with the required permissions and create a test record.
        """

        super().setUp()
        self.endpoint = lambda cid: reverse(
            "data.project.cid", kwargs={"code": "test", "cid": cid}
        )
        self.user = self.setup_user(
            "testuser", roles=["is_staff"], groups=["test.change.base"]
        )

        self.user.groups.add(Group.objects.get(name="test.add.base"))
        response = self.client.post(
            reverse("data.project", kwargs={"code": "test"}),
            data=next(iter(generate_test_data(n=1))),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.cid = response.json()["data"]["cid"]
        self.user.groups.remove(Group.objects.get(name="test.add.base"))

    def test_basic_ok(self):
        """
        Test update of a record by CID.
        """
        instance = TestModel.objects.get(cid=self.cid)
        updated_values = {
            "tests": instance.tests + 1,
            "text_option_2": instance.text_option_2 + "!",
        }
        response = self.client.patch(self.endpoint(self.cid), data=updated_values)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_instance = TestModel.objects.get(cid=self.cid)
        self.assertEqual(updated_instance.tests, updated_values["tests"])
        self.assertEqual(
            updated_instance.text_option_2, updated_values["text_option_2"]
        )
