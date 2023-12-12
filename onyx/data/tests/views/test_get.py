from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, generate_test_data, _test_record
from ...models.projects.test import TestModel


class TestGetView(OnyxTestCase):
    def setUp(self):
        """
        Create a user with the required permissions and create a test record.
        """

        super().setUp()
        self.endpoint = lambda cid: reverse(
            "data.project.cid", kwargs={"code": "test", "cid": cid}
        )
        self.user = self.setup_user(
            "testuser", roles=["is_staff"], groups=["test.view.base"]
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
        Test retrieval of a record by CID.
        """

        response = self.client.get(self.endpoint(self.cid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        _test_record(self, response.json()["data"], TestModel.objects.get(cid=self.cid))

    def test_include_ok(self):
        """
        Test retrieval of a record by CID with included fields.
        """

        response = self.client.get(self.endpoint(self.cid), data={"include": "cid"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"], {"cid": self.cid})

        response = self.client.get(
            self.endpoint(self.cid), data={"include": ["cid", "published_date"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["data"],
            {
                "cid": self.cid,
                "published_date": TestModel.objects.get(
                    cid=self.cid
                ).published_date.strftime("%Y-%m-%d"),
            },
        )

    def test_exclude_ok(self):
        """
        Test retrieval of a record by CID with excluded fields.
        """

        response = self.client.get(self.endpoint(self.cid), data={"exclude": "cid"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("cid", response.json()["data"])

        _test_record(
            self,
            response.json()["data"],
            TestModel.objects.get(cid=self.cid),
            created=True,
        )

        response = self.client.get(
            self.endpoint(self.cid), data={"exclude": ["cid", "published_date"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("cid", response.json()["data"])
        self.assertNotIn("published_date", response.json()["data"])
        _test_record(
            self,
            response.json()["data"],
            TestModel.objects.get(cid=self.cid),
            created=True,
        )

    def test_not_found_fail(self):
        """
        Test failure to retrieve a record that does not exist.
        """

        response = self.client.get(
            self.endpoint(f"C-{self.cid.removeprefix('C-')[::-1]}")
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_suppressed_not_found_fail(self):
        """
        Test failure to retrieve a record that has been suppressed.
        """

        instance = TestModel.objects.get(cid=self.cid)
        instance.suppressed = True
        instance.save()

        response = self.client.get(self.endpoint(self.cid))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
