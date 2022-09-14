from rest_framework.test import APITestCase
from rest_framework import status
from .models import Pathogen, Covid, Mpx
from .views import get_pathogen_model, enforce_optional_value_groups, enforce_field_set
from accounts.models import User, Institute
from utils.responses import APIResponse


class TestGetPathogenModel(APITestCase):
    def setUp(self):
        pass

    def test_get_pathogen_model(self):
        self.assertEqual(get_pathogen_model("pathogen", accept_base=True), Pathogen)
        self.assertEqual(get_pathogen_model("pathogen"), None)
        self.assertEqual(get_pathogen_model("covid"), Covid)
        self.assertEqual(get_pathogen_model("Covid"), Covid)
        self.assertEqual(get_pathogen_model("COVID"), Covid)
        self.assertEqual(get_pathogen_model("mpx"), Mpx)
        self.assertEqual(get_pathogen_model("COVOD"), None)


class TestEnforceOptionalValueGroups(APITestCase):
    def setUp(self):
        self.groups = list(Pathogen.OPTIONAL_VALUE_GROUPS)

    def test_enforce_optional_value_groups_ok(self):
        data = {"collection_month": "2022-01", "received_month": "2022-03"}
        self.assertEqual(enforce_optional_value_groups(data, self.groups), {})
        data.pop("collection_month")
        self.assertEqual(enforce_optional_value_groups(data, self.groups), {})

    def test_enforce_optional_value_groups_fail(self):
        data = {}
        self.groups.append(["published_date"])
        result = enforce_optional_value_groups(data, self.groups)

        self.assertNotEqual(enforce_optional_value_groups(data, self.groups), {})
        self.assertTrue("required_fields" in result)
        self.assertEqual(len(result["required_fields"]), 2)
        for results in result["required_fields"]:
            groups = list(results.values())
            for group in groups:
                self.assertTrue(
                    (("collection_month" in group) and ("received_month" in group))
                    or ("published_date" in group)
                )


class TestEnforceFieldSet(APITestCase):
    def setUp(self):
        self.accepted_fields = ["cid", "sender_sample_id", "run_name"]
        self.rejected_fields = ["id", "created"]

    def test_enforce_field_set_ok(self):
        data = {"cid": "C-123456", "sender_sample_id": "S-123456"}

        self.assertEqual(
            enforce_field_set(
                data=data,
                accepted_fields=self.accepted_fields,
                rejected_fields=self.rejected_fields,
            ),
            ({}, {}),
        )

    def test_enforce_field_set_fail(self):
        accepted_fields = ["cid", "sender_sample_id", "run_name"]
        rejected_fields = ["id", "created"]
        data = {
            "cid": "C-123456",
            "sender_sample_id": "S-123456",
            "id": 5,
            "created": "2022-01-01",
            "hi": "HELLO!!!!",
        }

        self.assertEqual(
            enforce_field_set(
                data=data,
                accepted_fields=accepted_fields,
                rejected_fields=rejected_fields,
            ),
            (
                {
                    "id": [APIResponse.NON_ACCEPTED_FIELD],
                    "created": [APIResponse.NON_ACCEPTED_FIELD],
                },
                {"hi": [APIResponse.UNKNOWN_FIELD]},
            ),
        )


class UserAPITestCase(APITestCase):
    def setup_authenticated_user(self, username, institute):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": username,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "institute": institute,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        self.client.force_authenticate(user)  # type: ignore
        return user

    def setup_approved_user(self, username, institute):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": username,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "institute": institute,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        user.is_approved = True
        self.client.force_authenticate(user)  # type: ignore
        return user

    def setup_authority_user(self, username, institute):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": username,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "institute": institute,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        user.is_approved = True
        user.is_authority = True
        self.client.force_authenticate(user)  # type: ignore
        return user

    def setup_admin_user(self, username, institute):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": username,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "institute": institute,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        user.is_staff = True
        self.client.force_authenticate(user)  # type: ignore
        return user
