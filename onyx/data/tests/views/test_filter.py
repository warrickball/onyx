from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, test_data
from ...models.projects.test import TestModel, TestModelRecord


class TestFilterView(OnyxTestCase):
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

        self.endpoint = reverse("data.filter", kwargs={"code": "test"})
        self.user.groups.remove(Group.objects.get(name="add.project.test"))

    def assertEqualCids(self, records, qs):
        record_values = sorted(record["cid"] for record in records)
        qs_values = sorted(qs.distinct().values_list("cid", flat=True))
        self.assertTrue(record_values)
        self.assertTrue(qs_values)
        self.assertEqual(
            record_values,
            qs_values,
        )

    def test_all_ok(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.all(),
        )

    def test_unknown_field_fail(self):
        response = self.client.get(self.endpoint, data={"hello": ":)"})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_choicefield_ok(self):
        response = self.client.get(self.endpoint, data={"country": "eng"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country="eng"),
        )

        response = self.client.get(self.endpoint, data={"country": "ENG"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country="eng"),
        )

    def test_choicefield_ne_ok(self):
        response = self.client.get(self.endpoint, data={"country__ne": "eng"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country__ne="eng"),
        )

    def test_choicefield_in_ok(self):
        response = self.client.get(self.endpoint, data={"country__in": "eng,wales"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country__in=["eng", "wales"]),
        )

    def test_choicefield_empty_ok(self):
        response = self.client.get(self.endpoint, data={"country": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country=""),
        )

    def test_choicefield_wronglookup_fail(self):
        response = self.client.get(self.endpoint, data={"country__range": "eng,wales"})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_choicefield_wrongchoice_fail(self):
        response = self.client.get(self.endpoint, data={"country": "ing"})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_relation_isnull_ok(self):
        response = self.client.get(self.endpoint, data={"records__isnull": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(records__isnull=True),
        )

        response = self.client.get(self.endpoint, data={"records__isnull": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(records__isnull=False),
        )

    def test_relation_wronglookup_fail(self):
        response = self.client.get(self.endpoint, data={"records": 1})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_charfield_ok(self):
        response = self.client.get(self.endpoint, data={"run_name": "run-1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(run_name="run-1"),
        )

    def test_charfield_ne_ok(self):
        response = self.client.get(self.endpoint, data={"run_name__ne": "run-1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(run_name__ne="run-1"),
        )

    def test_charfield_in_ok(self):
        response = self.client.get(
            self.endpoint, data={"run_name__in": "run-1,run-2,run-3"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(run_name__in=["run-1", "run-2", "run-3"]),
        )

    def test_charfield_range_ok(self):
        response = self.client.get(
            self.endpoint, data={"run_name__range": "run-0,run-9"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(response.json()["data"], TestModel.objects.all())

    def test_charfield_blank_ok(self):
        response = self.client.get(self.endpoint, data={"region": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"], TestModel.objects.filter(region="")
        )

        response = self.client.get(self.endpoint, data={"region__ne": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"], TestModel.objects.filter(region__ne="")
        )

    def test_charfield_contains_ok(self):
        response = self.client.get(self.endpoint, data={"run_name__contains": "run"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(response.json()["data"], TestModel.objects.all())

    def test_charfield_badlookup_fail(self):
        response = self.client.get(self.endpoint, data={"run_name__year": "2022"})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_number_ok(self):
        response = self.client.get(self.endpoint, data={"start": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(start=5),
        )
