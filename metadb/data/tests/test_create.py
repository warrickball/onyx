from rest_framework import status
from data.models import Covid
from accounts.models import Institute
from django.conf import settings
from data.tests.utils import METADBTestCase, get_covid_data


class TestCreatePathogen(METADBTestCase):
    def setUp(self):
        self.institute = Institute.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_admin_user("user", self.institute.code)

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
        pass  # TODO: Remove fields

    def test_create_empty_values(self):
        pass  # TODO: Keep fields but make values None/spaces/empty string

    def test_create_unknown_fields(self):
        pass  # TODO: Add fields such as id, created etc but also weird ones like HAHA

    def test_create_rejected_fields(self):
        pass  # TODO: Add fields such as cid
