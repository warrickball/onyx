from rest_framework import status
from data.models import Covid
from accounts.models import Institute
from django.conf import settings
from data.tests.utils import METADBTestCase, get_covid_data
from utils.responses import APIResponse
import os


class TestDeletePathogen(METADBTestCase):
    def setUp(self):
        self.institute = Institute.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_admin_user("user", self.institute.code)

        settings.CURSOR_PAGINATION_PAGE_SIZE = 20
        for _ in range(settings.CURSOR_PAGINATION_PAGE_SIZE * 5):
            covid_data = get_covid_data(self.institute)
            Covid.objects.create(**covid_data)

        self.cids = Covid.objects.values_list("cid", flat=True)

    def test_unauthenticated_delete(self):
        self.client.force_authenticate(user=None)  # type: ignore
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_delete(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authenticated_user(
                "authenticated-user", institute=self.institute.code
            )
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_delete(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_approved_user(
                "approved-user", institute=self.institute.code
            )
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authority_delete(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authority_user(
                "authority-user", institute=self.institute.code
            )
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_admin_user("admin-user", institute=self.institute.code)
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(Covid.objects.filter(cid=cid).exists() == False)

        results = self.client_get_paginated("/data/covid/")
        internal = Covid.objects.none()
        self.assertEqualCids(results, internal)

    def test_pathogen_not_found(self):
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/hello/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(
                response.json()["errors"], {"hello": APIResponse.NOT_FOUND}
            )

    def test_cid_not_found(self):
        response = self.client.delete(
            os.path.join("/data/covid/", "hello" + "/delete/")
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["errors"], {"hello": APIResponse.NOT_FOUND})
