from rest_framework import status
from data.models import Covid
from accounts.models import Site
from django.conf import settings
from data.tests.utils import METADBTestCase, get_covid_data
from utils.response import METADBAPIResponse
import secrets
import os


class TestUpdateGenomic(METADBTestCase):
    def setUp(self):
        self.site = Site.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.other_site = Site.objects.create(
            code="DEPTTHINGS", name="Department of Unimportant Things"
        )
        self.user = self.setup_admin_user("test-user", self.site.code)

        settings.CURSOR_PAGINATION_PAGE_SIZE = 20
        for _ in range(settings.CURSOR_PAGINATION_PAGE_SIZE * 5):
            covid_data = get_covid_data(self.site)
            Covid.objects.create(**covid_data)

        self.cids = Covid.objects.values_list("cid", flat=True)

    def test_unauthenticated_update(self):
        self.client.force_authenticate(user=None)  # type: ignore
        for cid in self.cids:
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"), data={"is_external": False}
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_update(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authenticated_user("authenticateduser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"), data={"is_external": False}
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_update(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_approved_user("approveduser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"), data={"is_external": False}
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authority_update(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authority_user("authorityuser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"), data={"is_external": False}
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_update(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_admin_user("adminuser", site=self.site.code)
        )
        for cid in self.cids:
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"), data={"is_external": False}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(Covid.objects.get(cid=cid).is_external == False)

    def test_pathogen_not_found(self):
        for cid in self.cids:
            response = self.client.patch(
                os.path.join("/data/hello/", cid + "/"), data={"is_external": False}
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(
                response.json()["errors"], {"hello": [METADBAPIResponse.NOT_FOUND]}
            )

    def test_cid_not_found(self):
        response = self.client.patch(
            os.path.join("/data/covid/", "hello" + "/"), data={"is_external": False}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["errors"], {"hello": [METADBAPIResponse.NOT_FOUND]}
        )

    def test_no_updates(self):
        cid = self.cids[0]
        response = self.client.patch(
            os.path.join(os.path.join("/data/covid/", cid + "/")),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_unknown_fields(self):
        for cid in self.cids:
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"),
                data={"is_external": False, "hello": "there"},
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(Covid.objects.get(cid=cid).is_external == False)
            self.assertTrue(
                response.json()["warnings"], {"hello": METADBAPIResponse.UNKNOWN_FIELD}
            )

    def test_update_rejected_fields(self):
        non_updaters = {
            "cid": f"C.{secrets.token_hex(3)}",
            "sample_id": f"S.{secrets.token_hex(3)}",
            "run_name": f"R.{secrets.token_hex(9)}",
            "project": "MPX",
            "published_date": "2022-01-01",
        }
        for cid in self.cids:
            for field, value in non_updaters.items():
                response = self.client.patch(
                    os.path.join("/data/covid/", cid + "/"),
                    data={
                        "fasta_path": "/updated/fasta/path.fasta",
                        field: value,
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertTrue(
                    Covid.objects.get(cid=cid).fasta_path != "/updated/fasta/path.fasta"
                )
                self.assertTrue(
                    response.json()["errors"],
                    {field: METADBAPIResponse.NON_ACCEPTED_FIELD},
                )

    def test_update_unknown_and_rejected_fields(self):
        non_updaters = {
            "cid": f"C.{secrets.token_hex(3)}",
            "sample_id": f"S.{secrets.token_hex(3)}",
            "run_name": f"R.{secrets.token_hex(9)}",
            "project": "MPX",
            "published_date": "2022-01-01",
            "site": "DEPTTHINGS",
        }
        for cid in self.cids:
            for field, value in non_updaters.items():
                response = self.client.patch(
                    os.path.join("/data/covid/", cid + "/"),
                    data={
                        "fasta_path": "/updated/fasta/path.fasta",
                        field: value,
                        "hello": "there",
                    },
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertTrue(
                    Covid.objects.get(cid=cid).fasta_path != "/updated/fasta/path.fasta"
                )
                self.assertTrue(
                    response.json()["errors"],
                    {field: METADBAPIResponse.NON_ACCEPTED_FIELD},
                )
                self.assertTrue(
                    response.json()["warnings"],
                    {"hello": METADBAPIResponse.UNKNOWN_FIELD},
                )

    def test_update_empty_values(self):
        for cid in self.cids:
            is_external = Covid.objects.get(cid=cid).is_external
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"), data={"is_external": ""}
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Covid.objects.get(cid=cid).is_external, is_external)

            # Blank text field is not allowed!! Great!!
            fasta_path = Covid.objects.get(cid=cid).fasta_path
            response = self.client.patch(
                os.path.join("/data/covid/", cid + "/"), data={"fasta_path": ""}
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Covid.objects.get(cid=cid).fasta_path, fasta_path)

    def test_update_optional_value_groups(self):
        for cid in self.cids:
            instance = Covid.objects.get(cid=cid)
            if instance.collection_month and instance.received_month:
                response = self.client.patch(
                    os.path.join("/data/covid/", cid + "/"),
                    data={"collection_month": ""},
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                response = self.client.patch(
                    os.path.join("/data/covid/", cid + "/"), data={"received_month": ""}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            elif instance.collection_month:
                response = self.client.patch(
                    os.path.join("/data/covid/", cid + "/"),
                    data={"collection_month": ""},
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            elif instance.received_month:
                response = self.client.patch(
                    os.path.join("/data/covid/", cid + "/"), data={"received_month": ""}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            else:
                self.assertEqual(True, False)
