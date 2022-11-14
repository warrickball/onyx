from rest_framework import status
from data.models import Covid
from accounts.models import Site
from django.conf import settings
from data.tests.utils import METADBTestCase, get_covid_data
from utils.responses import METADBAPIResponse
import os


class TestDeletePathogen(METADBTestCase):
    def setUp(self):
        self.site = Site.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_admin_user("test-user", self.site.code)

        settings.CURSOR_PAGINATION_PAGE_SIZE = 20
        for _ in range(settings.CURSOR_PAGINATION_PAGE_SIZE * 5):
            covid_data = get_covid_data(self.site)
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
            user=self.setup_authenticated_user("authenticateduser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_delete(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_approved_user("approveduser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authority_delete(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authority_user("authorityuser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_admin_user("adminuser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.delete(
                os.path.join("/data/covid/", cid + "/delete/")
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(Covid.objects.filter(cid=cid).exists())

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
                response.json()["errors"], {"hello": METADBAPIResponse.NOT_FOUND}
            )

    def test_cid_not_found(self):
        response = self.client.delete(
            os.path.join("/data/covid/", "hello" + "/delete/")
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["errors"], {"hello": METADBAPIResponse.NOT_FOUND}
        )
