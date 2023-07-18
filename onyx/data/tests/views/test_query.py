from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, test_data
from ...models.projects.test import TestModel, TestModelRecord


class TestQueryView(OnyxTestCase):
    def setUp(self):
        super().setUp()
        self.endpoint = reverse("data.create", kwargs={"code": "test"})
        self.user = self.setup_user(
            "testuser",
            roles=["is_staff"],
            groups=[
                "add.project.test",
                "view.project.test",
            ],
        )
        for payload in test_data():
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.endpoint = reverse("data.query", kwargs={"code": "test"})
        self.user.groups.remove(Group.objects.get(name="add.project.test"))
