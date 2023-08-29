from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, test_data


class TestQueryView(OnyxTestCase):
    def setUp(self):
        super().setUp()
        self.endpoint = reverse("data.project", kwargs={"code": "test"})
        self.user = self.setup_user(
            "testuser",
            roles=["is_staff"],
            groups=[
                "test.add.base",
                "test.view.base",
            ],
        )
        for payload in test_data():
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.endpoint = reverse("data.project.query", kwargs={"code": "test"})
        self.user.groups.remove(Group.objects.get(name="test.add.base"))
