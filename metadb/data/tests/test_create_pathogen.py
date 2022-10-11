from rest_framework import status
from data.models import Covid
from accounts.models import Institute
from django.conf import settings
from data.tests.utils import METADBTestCase, get_covid_data
from utils.responses import METADBAPIResponse
import secrets
import random


class TestCreatePathogen(METADBTestCase):
    def setUp(self):
        self.institute = Institute.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_admin_user("test-user", self.institute.code)

        settings.CURSOR_PAGINATION_PAGE_SIZE = 20
        self.covid_data = []
        for _ in range(settings.CURSOR_PAGINATION_PAGE_SIZE * 5):
            self.covid_data.append(get_covid_data(self.institute.code))

    def test_unauthenticated_create(self):
        self.client.force_authenticate(user=None)  # type: ignore
        response = self.client.post("/data/covid/", data=self.covid_data[0])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_create(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authenticated_user(
                "authenticated-user", institute=self.institute.code
            )
        )
        response = self.client.post("/data/covid/", data=self.covid_data[0])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_create(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_approved_user(
                "approved-user", institute=self.institute.code
            )
        )
        response = self.client.post("/data/covid/", data=self.covid_data[0])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authority_create(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authority_user(
                "authority-user", institute=self.institute.code
            )
        )
        response = self.client.post("/data/covid/", data=self.covid_data[0])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_create(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_admin_user("admin-user", institute=self.institute.code)
        )
        response = self.client.post("/data/covid/", data=self.covid_data[0])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        cid = results[0]["cid"]
        self.assertTrue(Covid.objects.filter(cid=cid).exists())

    def test_pathogen_not_found(self):
        for x in self.covid_data:
            response = self.client.post("/data/hello/", data=x)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(
                response.json()["errors"], {"hello": METADBAPIResponse.NOT_FOUND}
            )

    def test_create(self):
        results = []
        for x in self.covid_data:
            response = self.client.post("/data/covid/", data=x)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_results = response.json()["results"]
            self.assertEqual(len(response_results), 1)
            results.append(response_results[0])

        internal = Covid.objects.all()
        self.assertEqualCids(results, internal)

    def test_create_missing_fields(self):
        for x in self.covid_data:
            for field in [
                "sender_sample_id",
                "run_name",
                "institute",
                "fasta_path",
                "bam_path",
            ]:
                x_ = dict(x)
                x_.pop(field)

                response = self.client.post("/data/covid/", data=x_)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_empty_values(self):
        for x in self.covid_data:
            for field in [
                "sender_sample_id",
                "run_name",
                "institute",
                "fasta_path",
                "bam_path",
            ]:
                x_ = dict(x)
                for bad in ["", " ", "              "]:
                    x_[field] = bad
                    response = self.client.post("/data/covid/", data=x_)
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_unknown_fields(self):
        results = []
        for x in self.covid_data:
            x_ = dict(x)
            x_["id"] = 42
            x_["HELLO"] = "GOOD DAY"
            response = self.client.post("/data/covid/", data=x_)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(
                response.json()["warnings"],
                {
                    "id": [METADBAPIResponse.UNKNOWN_FIELD],
                    "HELLO": [METADBAPIResponse.UNKNOWN_FIELD],
                },
            )
            response_results = response.json()["results"]
            self.assertEqual(len(response_results), 1)
            results.append(response_results[0])
        internal = Covid.objects.all()
        self.assertEqualCids(results, internal)

    def test_create_rejected_fields(self):
        for x in self.covid_data:
            x_ = dict(x)
            x_["cid"] = f"C-{secrets.token_hex(3)}"
            x_["published_date"] = "2022-01-01"
            response = self.client.post("/data/covid/", data=x_)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.json()["errors"],
                {
                    "cid": [METADBAPIResponse.NON_ACCEPTED_FIELD],
                    "published_date": [METADBAPIResponse.NON_ACCEPTED_FIELD],
                },
            )

    def test_create_unknown_and_rejected_fields(self):
        for x in self.covid_data:
            x_ = dict(x)
            x_["id"] = 42
            x_["HELLO"] = "GOOD DAY"
            x_["cid"] = f"C-{secrets.token_hex(3)}"
            x_["published_date"] = "2022-01-01"
            response = self.client.post("/data/covid/", data=x_)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.json()["warnings"],
                {
                    "id": [METADBAPIResponse.UNKNOWN_FIELD],
                    "HELLO": [METADBAPIResponse.UNKNOWN_FIELD],
                },
            )
            self.assertEqual(
                response.json()["errors"],
                {
                    "cid": [METADBAPIResponse.NON_ACCEPTED_FIELD],
                    "published_date": [METADBAPIResponse.NON_ACCEPTED_FIELD],
                },
            )

    def test_create_optional_value_groups(self):
        for x in self.covid_data:
            x_ = dict(x)
            x_.pop("collection_month", None)
            x_.pop("received_month", None)
            response = self.client.post("/data/covid/", data=x_)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            x_ = dict(x)
            if x.get("collection_month") and x.get("received_month"):
                coin = random.randint(0, 1)
                if coin:
                    x_.pop("collection_month", None)
                else:
                    x_.pop("received_month", None)
            response = self.client.post("/data/covid/", data=x_)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_mismatch_pathogen_code(self):
        for x in self.covid_data:
            x["pathogen_code"] = "PATHOGEN"
            response = self.client.post("/data/covid/", data=x)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(len(Covid.objects.all()) == 0)

    def test_sample_and_run_preexisting(self):
        results = []
        for x in self.covid_data:
            response = self.client.post("/data/covid/", data=x)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_results = response.json()["results"]
            self.assertEqual(len(response_results), 1)
            results.append(response_results[0])

        internal = Covid.objects.all()
        self.assertEqualCids(results, internal)

        for x in self.covid_data:
            response = self.client.post("/data/covid/", data=x)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sample_or_run_preexisting(self):
        results = []
        for x in self.covid_data:
            response = self.client.post("/data/covid/", data=x)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_results = response.json()["results"]
            self.assertEqual(len(response_results), 1)
            results.append(response_results[0])

        internal = Covid.objects.all()
        self.assertEqualCids(results, internal)

        for x in self.covid_data:
            x_ = dict(x)
            coin = random.randint(0, 1)
            if coin:
                x_["sender_sample_id"] = f"S-{secrets.token_hex(4)}"
            else:
                x_["run_name"] = f"R-{secrets.token_hex(9)}"
            response = self.client.post("/data/covid/", data=x_)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_results = response.json()["results"]
            self.assertEqual(len(response_results), 1)
            results.append(response_results[0])

        internal = Covid.objects.all()
        self.assertEqualCids(results, internal)
