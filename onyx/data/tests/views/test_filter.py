from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase, generate_test_data
from ...models.projects.test import TestModel


# TODO: Test for filtering
# Need to test summarise function, all OnyxTypes, and the effect of suppressing data


class TestFilterView(OnyxTestCase):
    def setUp(self):
        """
        Create a user with the required permissions and create a set of test records.
        """

        super().setUp()
        self.endpoint = reverse("data.project", kwargs={"code": "test"})
        self.user = self.setup_user(
            "testuser", roles=["is_staff"], groups=["test.view.base"]
        )

        self.user.groups.add(Group.objects.get(name="test.add.base"))
        for payload in generate_test_data():
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.groups.remove(Group.objects.get(name="test.add.base"))

    def assertEqualCids(self, records, qs):
        """
        Assert that the CIDs in the records match the CIDs in the queryset.
        """

        record_values = sorted(record["cid"] for record in records)
        qs_values = sorted(qs.distinct().values_list("cid", flat=True))
        self.assertTrue(record_values)
        self.assertTrue(qs_values)
        self.assertEqual(
            record_values,
            qs_values,
        )

    def test_basic(self):
        """
        Test basic retrieval of all records.
        """

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.all(),
        )

    def test_unknown_field(self):
        """
        Test that filtering on an unknown field fails.
        """

        response = self.client.get(self.endpoint, data={"hello": ":)"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_choicefield(self):
        """
        Test filtering on a choice field.
        """

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

    def test_choicefield_ne(self):
        """
        Test filtering on a choice field with the ne lookup.
        """

        response = self.client.get(self.endpoint, data={"country__ne": "eng"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country__ne="eng"),
        )

    def test_choicefield_in(self):
        """
        Test filtering on a choice field with the in lookup.
        """

        response = self.client.get(self.endpoint, data={"country__in": "eng,wales"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country__in=["eng", "wales"]),
        )

    def test_choicefield_empty(self):
        """
        Test filtering on a choice field with an empty value.
        """

        response = self.client.get(self.endpoint, data={"country": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(country=""),
        )

    def test_choicefield_wronglookup(self):
        """
        Test filtering on a choice field with an invalid lookup.
        """

        response = self.client.get(self.endpoint, data={"country__range": "eng,wales"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_choicefield_wrongchoice(self):
        """
        Test filtering on a choice field with an invalid choice.
        """

        response = self.client.get(self.endpoint, data={"country": "ing"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_relation_isnull(self):
        """
        Test filtering on a relation field with the isnull lookup.
        """

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

    def test_relation_wronglookup(self):
        """
        Test filtering on a relation field with an invalid lookup.
        """

        response = self.client.get(self.endpoint, data={"records": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_charfield(self):
        """
        Test filtering on a text field.
        """

        response = self.client.get(self.endpoint, data={"run_name": "run-1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(run_name="run-1"),
        )

    def test_charfield_ne(self):
        """
        Test filtering on a text field with the ne lookup.
        """

        response = self.client.get(self.endpoint, data={"run_name__ne": "run-1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(run_name__ne="run-1"),
        )

    def test_charfield_in(self):
        """
        Test filtering on a text field with the in lookup.
        """

        response = self.client.get(
            self.endpoint, data={"run_name__in": "run-1,run-2,run-3"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(run_name__in=["run-1", "run-2", "run-3"]),
        )

    def test_charfield_blank(self):
        """
        Test filtering on a text field with an empty value.
        """

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

    def test_charfield_contains(self):
        """
        Test filtering on a text field with the contains lookup.
        """

        response = self.client.get(self.endpoint, data={"run_name__contains": "run"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(response.json()["data"], TestModel.objects.all())

    def test_charfield_badlookup(self):
        """
        Test filtering on a text field with an invalid lookup.
        """

        response = self.client.get(self.endpoint, data={"run_name__year": "2022"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_integer(self):
        """
        Test filtering on a integer field.
        """

        response = self.client.get(self.endpoint, data={"start": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqualCids(
            response.json()["data"],
            TestModel.objects.filter(start=5),
        )
