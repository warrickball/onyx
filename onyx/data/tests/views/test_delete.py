from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, generate_test_data, _test_record
from ...models.projects.test import TestModel


# TODO: Tests for delete endpoint
class TestDeleteView(OnyxTestCase):
    def setUp(self):
        """
        Create a user with the required permissions and create a test record.
        """

        super().setUp()
        self.endpoint = lambda cid: reverse(
            "data.project.cid", kwargs={"code": "test", "cid": cid}
        )
        self.user = self.setup_user(
            "testuser", roles=["is_staff"], groups=["test.delete.base"]
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
        Test deletion of a record by CID.
        """

        response = self.client.delete(self.endpoint(self.cid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(TestModel.objects.filter(cid=self.cid).exists())
