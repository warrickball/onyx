from rest_framework import status
from data.models import Covid
from accounts.models import Site
from django.conf import settings
from data.tests.utils import METADBTestCase, get_covid_data


class TestGetProject(METADBTestCase):
    def setUp(self):
        self.site = Site.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_approved_user("testuser", self.site.code)

        settings.CURSOR_PAGINATION_PAGE_SIZE = 20
        for _ in range(settings.CURSOR_PAGINATION_PAGE_SIZE * 5):
            covid_data = get_covid_data(self.site)
            Covid.objects.create(**covid_data)

    def test_unauthenticated_get(self):
        self.client.force_authenticate(user=None)  # type: ignore
        results = self.client_get_paginated(
            "/data/pathogens/", expected_status_code=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authenticated_user("authenticateduser", site=self.site.code)
        )
        results = self.client_get_paginated(
            "/data/pathogens/", expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_approved_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_approved_user("approveduser", site=self.site.code)
        )
        results = self.client_get_paginated(
            "/data/pathogens/", expected_status_code=status.HTTP_200_OK
        )

    def test_authority_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authority_user("authorityuser", site=self.site.code)
        )
        results = self.client_get_paginated(
            "/data/pathogens/", expected_status_code=status.HTTP_200_OK
        )

    def test_admin_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_admin_user("adminuser", site=self.site.code)
        )
        results = self.client_get_paginated(
            "/data/pathogens/", expected_status_code=status.HTTP_200_OK
        )
