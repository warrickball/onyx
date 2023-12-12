from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, generate_test_data


# TODO: Tests for query endpoint


class TestQueryView(OnyxTestCase):
    def setUp(self):
        super().setUp()
        self.endpoint = reverse("data.project", kwargs={"code": "test"})
        self.user = self.setup_user(
            "testuser",
            roles=["is_staff"],
            groups=[
                "test.view.base",
            ],
        )

        self.user.groups.add(Group.objects.get(name="test.add.base"))
        for payload in generate_test_data():
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.groups.remove(Group.objects.get(name="test.add.base"))

        self.endpoint = reverse("data.project.query", kwargs={"code": "test"})
