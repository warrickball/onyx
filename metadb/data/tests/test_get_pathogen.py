from rest_framework import status
from data.models import Covid
from accounts.models import Site
from data.filters import BASE_LOOKUPS, CHAR_LOOKUPS
from utils.responses import METADBAPIResponse
from django.conf import settings
from datetime import date
from data.tests.utils import METADBTestCase, get_covid_data


class TestGetPathogen(METADBTestCase):
    def setUp(self):
        self.site = Site.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_approved_user("test-user", self.site.code)

        settings.CURSOR_PAGINATION_PAGE_SIZE = 20
        for _ in range(settings.CURSOR_PAGINATION_PAGE_SIZE * 5):
            covid_data = get_covid_data(self.site)
            Covid.objects.create(**covid_data)

    def test_unauthenticated_get(self):
        self.client.force_authenticate(user=None)  # type: ignore
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authenticated_user(
                "authenticated-user", site=self.site.code
            )
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_approved_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_approved_user("approved-user", site=self.site.code)
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_200_OK
        )

    def test_authority_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authority_user("authority-user", site=self.site.code)
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_200_OK
        )

    def test_admin_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_admin_user("admin-user", site=self.site.code)
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_200_OK
        )

    def test_pathogen_not_found(self):
        response = self.client.get("/data/hello/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["errors"], {"hello": METADBAPIResponse.NOT_FOUND}
        )

    def test_get(self):
        results = self.client_get_paginated(
            "/data/covid/",
        )
        internal = Covid.objects.all()
        self.assertEqualCids(results, internal)

    def test_field_mix(self):
        results = self.client_get_paginated(
            "/data/covid/",
            data={
                "cid__contains": ["1", "A"],
                "collection_month__range": ["2021-01,2022-01", "2021-09,2022-03"],
                "fasta_header__in": ["MN908947.3,hello,goodbye", "NC_045512,hello"],
                "received_month__lte": ["2022-01", "2021-08"],
            },
        )
        internal = (
            Covid.objects.filter(cid__contains="1")
            .filter(cid__contains="A")
            .filter(collection_month__range=["2021-01", "2022-01"])
            .filter(collection_month__range=["2021-09", "2022-03"])
            .filter(fasta_header__in=["MN908947.3", "hello", "goodbye"])
            .filter(fasta_header__in=["NC_045512", "hello"])
            .filter(received_month__lte="2022-01")
            .filter(received_month__lte="2021-08")
        )
        self.assertEqualCids(results, internal)

    def test_get_unknown_fields(self):
        response = self.client.get(
            "/data/covid/",
            data={"HI THERE": "HELLO!!!!!!!!!!!!!!!!", "BYE THERE": "WEEEEEEEEEEEEEE"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            {
                "HI THERE": [METADBAPIResponse.UNKNOWN_FIELD],
                "BYE THERE": [METADBAPIResponse.UNKNOWN_FIELD],
            },
        )

        response = self.client.get(
            "/data/covid/",
            data={"is_external": True, "hello": "there", "hi": ["hi", "bye"]},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"],
            {
                "hello": [METADBAPIResponse.UNKNOWN_FIELD],
                "hi": [METADBAPIResponse.UNKNOWN_FIELD],
            },
        )


class TestGetPathogenChoiceField(TestGetPathogen):
    def test_choice_field_exact(self):
        for value in ["SWAB", "SERUM"]:
            results = self.client_get_paginated(
                "/data/covid/", data={"sample_type": value}
            )
            internal = Covid.objects.filter(sample_type=value)
            self.assertEqualCids(results, internal)

    def test_choice_field_in(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"sample_type__in": ["SWAB,SERUM"]}
        )
        internal = Covid.objects.filter(sample_type__in=["SWAB", "SERUM"])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={"sample_type__in": ["SWAB,SERUM", "SWAB"]},
        )
        internal = Covid.objects.filter(sample_type__in=["SWAB", "SERUM"]).filter(
            sample_type__in=["SWAB"]
        )
        self.assertEqualCids(results, internal)

    def test_choice_field_notin(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"sample_type__notin": ["SWAB,SERUM"]}
        )
        internal = Covid.objects.exclude(sample_type__in=["SWAB", "SERUM"])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={"sample_type__notin": ["SWAB", "SERUM"]},
        )
        internal = Covid.objects.exclude(sample_type__in=["SWAB"]).exclude(
            sample_type__in=["SERUM"]
        )
        self.assertEqualCids(results, internal)

    def test_choice_field_range(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"sample_type__range": ["SERUM,SWAB"]}
        )
        internal = Covid.objects.filter(sample_type__range=["SERUM", "SWAB"])
        self.assertEqualCids(results, internal)

    def test_choice_field_isnull(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"sample_type__isnull": ["true"]}
        )
        internal = Covid.objects.filter(sample_type__isnull=True)
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/", data={"sample_type__isnull": ["false"]}
        )
        internal = Covid.objects.filter(sample_type__isnull=False)
        self.assertEqualCids(results, internal)

    def test_choice_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            results = self.client_get_paginated(
                "/data/covid/", data={f"sample_type__{lookup}": ["SWAB"]}
            )
            internal = Covid.objects.filter(**{f"sample_type__{lookup}": "SWAB"})
            self.assertEqualCids(results, internal)

    def test_choice_field_char_lookups(self):
        for lookup in CHAR_LOOKUPS:
            results = self.client_get_paginated(
                "/data/covid/", data={f"sample_type__{lookup}": ["SWAB"]}
            )
            internal = Covid.objects.filter(**{f"sample_type__{lookup}": "SWAB"})
            self.assertEqualCids(results, internal)

    def test_choice_field_non_choice(self):
        for value in ["HELLO THERE", "SWA", "SER"]:
            # Exact
            results = self.client_get_paginated(
                "/data/covid/",
                data={"sample_type": value},
                expected_status_code=status.HTTP_400_BAD_REQUEST,
            )

            # Base lookups
            for lookup in BASE_LOOKUPS:
                results = self.client_get_paginated(
                    "/data/covid/",
                    data={f"sample_type__{lookup}": [value]},
                    expected_status_code=status.HTTP_400_BAD_REQUEST,
                )

    def test_choice_field_non_choice_but_char_lookup_so_its_all_cool(self):
        for value in ["HELLO THERE", "SWA", "SER"]:
            for lookup in CHAR_LOOKUPS:
                results = self.client_get_paginated(
                    "/data/covid/", data={f"sample_type__{lookup}": [value]}
                )
                internal = Covid.objects.filter(**{f"sample_type__{lookup}": value})
                self.assertEqualCids(results, internal)


class TestGetPathogenCharField(TestGetPathogen):
    def test_char_field_exact(self):
        for value in ["MN908947.3", "NC_045512", "hello", "goodbye"]:
            results = self.client_get_paginated(
                "/data/covid/", data={"fasta_header": value}
            )
            internal = Covid.objects.filter(fasta_header=value)
            self.assertEqualCids(results, internal)

    def test_char_field_in(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"fasta_header__in": ["NC_045512,hello"]}
        )
        internal = Covid.objects.filter(fasta_header__in=["NC_045512", "hello"])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={"fasta_header__in": ["NC_045512,hello", "MN908947.3,hello"]},
        )
        internal = Covid.objects.filter(fasta_header__in=["NC_045512", "hello"]).filter(
            fasta_header__in=["MN908947.3", "hello"]
        )
        self.assertEqualCids(results, internal)

    def test_char_field_notin(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"fasta_header__notin": ["NC_045512,hello"]}
        )
        internal = Covid.objects.exclude(fasta_header__in=["NC_045512", "hello"])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={"fasta_header__notin": ["NC_045512,hello", "MN908947.3,hello"]},
        )
        internal = Covid.objects.exclude(
            fasta_header__in=["NC_045512", "hello"]
        ).exclude(fasta_header__in=["MN908947.3", "hello"])
        self.assertEqualCids(results, internal)

    def test_char_field_range(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"fasta_header__range": ["goodbye,hello"]}
        )
        internal = Covid.objects.filter(fasta_header__range=["goodbye", "hello"])
        self.assertEqualCids(results, internal)

    def test_char_field_isnull(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"fasta_header__isnull": ["true"]}
        )
        internal = Covid.objects.filter(fasta_header__isnull=True)
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/", data={"fasta_header__isnull": ["false"]}
        )
        internal = Covid.objects.filter(fasta_header__isnull=False)
        self.assertEqualCids(results, internal)

    def test_char_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            results = self.client_get_paginated(
                "/data/covid/", data={f"fasta_header__{lookup}": ["hello"]}
            )
            internal = Covid.objects.filter(**{f"fasta_header__{lookup}": "hello"})
            self.assertEqualCids(results, internal)

    def test_char_field_char_lookups(self):
        for lookup in CHAR_LOOKUPS:
            results = self.client_get_paginated(
                "/data/covid/", data={f"fasta_header__{lookup}": ["hello"]}
            )
            internal = Covid.objects.filter(**{f"fasta_header__{lookup}": "hello"})
            self.assertEqualCids(results, internal)


class TestGetPathogenYearMonthField(TestGetPathogen):
    def test_yearmonth_field_exact(self):
        for value in ["2021-03", "2022-01", "2022-04", "2022-12"]:
            results = self.client_get_paginated(
                "/data/covid/", data={"collection_month": value}
            )
            internal = Covid.objects.filter(collection_month=value)
            self.assertEqualCids(results, internal)

    def test_yearmonth_field_in(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__in": ["2021-03,2022-04"]}
        )
        internal = Covid.objects.filter(collection_month__in=["2021-03", "2022-04"])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={"collection_month__in": ["2021-03,2022-04", "2022-01,2022-04"]},
        )
        internal = Covid.objects.filter(
            collection_month__in=["2021-03", "2022-04"]
        ).filter(collection_month__in=["2022-01", "2022-04"])
        self.assertEqualCids(results, internal)

    def test_yearmonth_field_notin(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__notin": ["2021-03,2022-04"]}
        )
        internal = Covid.objects.exclude(collection_month__in=["2021-03", "2022-04"])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={"collection_month__notin": ["2021-03,2022-04", "2022-01,2022-04"]},
        )
        internal = Covid.objects.exclude(
            collection_month__in=["2021-03", "2022-04"]
        ).exclude(collection_month__in=["2022-01", "2022-04"])
        self.assertEqualCids(results, internal)

    def test_yearmonth_field_range(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__range": ["2021-03,2022-04"]}
        )
        internal = Covid.objects.filter(collection_month__range=["2021-03", "2022-04"])
        self.assertEqualCids(results, internal)

    def test_yearmonth_field_isnull(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__isnull": ["true"]}
        )
        internal = Covid.objects.filter(collection_month__isnull=True)
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__isnull": ["false"]}
        )
        internal = Covid.objects.filter(collection_month__isnull=False)
        self.assertEqualCids(results, internal)

    def test_yearmonth_field_iso_year(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__iso_year": ["2022"]}
        )
        internal = Covid.objects.filter(collection_month__iso_year=2022)
        self.assertEqualCids(results, internal)

    def test_yearmonth_field_iso_year_in(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__iso_year__in": ["2021,2022"]}
        )
        internal = Covid.objects.filter(collection_month__iso_year__in=[2021, 2022])
        self.assertEqualCids(results, internal)

    def test_yearmonth_field_iso_year_range(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"collection_month__iso_year__range": ["2021,2022"]}
        )
        internal = Covid.objects.filter(collection_month__iso_year__range=[2021, 2022])
        self.assertEqualCids(results, internal)

    def test_yearmonth_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            results = self.client_get_paginated(
                "/data/covid/", data={f"collection_month__{lookup}": ["2022-04"]}
            )
            internal = Covid.objects.filter(
                **{f"collection_month__{lookup}": "2022-04"}
            )
            self.assertEqualCids(results, internal)

    def test_yearmonth_invalid_yearmonth(self):
        for value in [
            "2021-",
            "-01",
            "HELLO-THERE",
            "2022-HEELLOOOTHHEEEERREEE!!!",
            "2022-01-01",
            "2022",
            "2022-01-01-01-01-01",
            "202222222222222222222222222222222-1",
            "1-1",
        ]:
            # Exact
            results = self.client_get_paginated(
                "/data/covid/",
                data={"collection_month": value},
                expected_status_code=status.HTTP_400_BAD_REQUEST,
            )

            # Base lookups
            for lookup in BASE_LOOKUPS:
                results = self.client_get_paginated(
                    "/data/covid/",
                    data={f"collection_month__{lookup}": [value]},
                    expected_status_code=status.HTTP_400_BAD_REQUEST,
                )


class TestGetPathogenDateField(TestGetPathogen):
    def setUp(self):
        super().setUp()

        today = date.today()
        year, week, day = today.isocalendar()
        self.today = str(today)
        self.today_week = week

    def test_date_field_exact(self):
        for value in ["2021-03-04", "2022-01-01", self.today, "2022-12-25"]:
            results = self.client_get_paginated(
                "/data/covid/", data={"published_date": value}
            )
            internal = Covid.objects.filter(published_date=value)
            self.assertEqualCids(results, internal)

    def test_date_field_in(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__in": [f"2021-03-04,{self.today}"]}
        )
        internal = Covid.objects.filter(published_date__in=["2021-03-04", self.today])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={
                "published_date__in": [
                    f"2021-03-04,{self.today}",
                    f"2022-01-01,{self.today}",
                ]
            },
        )
        internal = Covid.objects.filter(
            published_date__in=["2021-03-04", self.today]
        ).filter(published_date__in=["2022-01-01", self.today])
        self.assertEqualCids(results, internal)

    def test_date_field_notin(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__notin": [f"2021-03-04,{self.today}"]}
        )
        internal = Covid.objects.exclude(published_date__in=["2021-03-04", self.today])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={
                "published_date__notin": [
                    f"2021-03-04,{self.today}",
                    f"2022-01-01,{self.today}",
                ]
            },
        )
        internal = Covid.objects.exclude(
            published_date__in=["2021-03-04", self.today]
        ).exclude(published_date__in=["2022-01-01", self.today])
        self.assertEqualCids(results, internal)

    def test_date_field_range(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__range": [f"2021-03-04,{self.today}"]}
        )
        internal = Covid.objects.filter(
            published_date__range=["2021-03-04", self.today]
        )
        self.assertEqualCids(results, internal)

    def test_date_field_isnull(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__isnull": ["true"]}
        )
        internal = Covid.objects.filter(published_date__isnull=True)
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__isnull": ["false"]}
        )
        internal = Covid.objects.filter(published_date__isnull=False)
        self.assertEqualCids(results, internal)

    def test_date_field_iso_year(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__iso_year": ["2022"]}
        )
        internal = Covid.objects.filter(published_date__iso_year=2022)
        self.assertEqualCids(results, internal)

    def test_date_field_iso_year_in(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__iso_year__in": ["2021,2022"]}
        )
        internal = Covid.objects.filter(published_date__iso_year__in=[2021, 2022])
        self.assertEqualCids(results, internal)

    def test_date_field_iso_year_range(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__iso_year__range": ["2021,2022"]}
        )
        internal = Covid.objects.filter(published_date__iso_year__range=[2021, 2022])
        self.assertEqualCids(results, internal)

    def test_date_field_iso_week(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"published_date__iso_week": [str(self.today_week)]}
        )
        internal = Covid.objects.filter(published_date__week=self.today_week)
        self.assertEqualCids(results, internal)

    def test_date_field_iso_week_in(self):
        results = self.client_get_paginated(
            "/data/covid/",
            data={"published_date__iso_week__in": [f"{str(self.today_week)},11"]},
        )
        internal = Covid.objects.filter(published_date__week__in=[self.today_week, 11])
        self.assertEqualCids(results, internal)

    def test_date_field_iso_week_range(self):
        results = self.client_get_paginated(
            "/data/covid/",
            data={"published_date__iso_week__range": [f"11,{str(self.today_week)}"]},
        )
        internal = Covid.objects.filter(
            published_date__week__range=[11, self.today_week]
        )
        self.assertEqualCids(results, internal)

    def test_date_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            results = self.client_get_paginated(
                "/data/covid/", data={f"published_date__{lookup}": [self.today]}
            )
            internal = Covid.objects.filter(**{f"published_date__{lookup}": self.today})
            self.assertEqualCids(results, internal)

    def test_date_field_invalid_date(self):
        for value in [
            "2021-",
            "-01",
            "HELLO-THERE",
            "2022-HEELLOOOTHHEEEERREEE!!!",
            "2022-01",
            "2022",
            "2022-01-01-01-01-01",
            "20222222222222222222222-01-01",
            "1-1-1",
        ]:
            # Exact
            results = self.client_get_paginated(
                "/data/covid/",
                data={"published_date": value},
                expected_status_code=status.HTTP_400_BAD_REQUEST,
            )

            # Base lookups
            for lookup in BASE_LOOKUPS:
                results = self.client_get_paginated(
                    "/data/covid/",
                    data={f"published_date__{lookup}": [value]},
                    expected_status_code=status.HTTP_400_BAD_REQUEST,
                )


class TestGetPathogenBooleanField(TestGetPathogen):
    def test_boolean_field(self):
        for value in ["true", "True"]:
            results = self.client_get_paginated(
                "/data/covid/", data={"is_external": value}
            )
            internal = Covid.objects.filter(is_external=True)
            self.assertEqualCids(results, internal)

        for value in ["false", "False"]:
            results = self.client_get_paginated(
                "/data/covid/", data={"is_external": value}
            )
            internal = Covid.objects.filter(is_external=False)
            self.assertEqualCids(results, internal)

    def test_boolean_field_in(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"is_external__in": ["true,false"]}
        )
        internal = Covid.objects.filter(is_external__in=[True, False])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={
                "is_external__in": [
                    "true,False",
                    "false",
                ]
            },
        )
        internal = Covid.objects.filter(is_external__in=[True, False]).filter(
            is_external__in=[False]
        )
        self.assertEqualCids(results, internal)

    def test_boolean_field_notin(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"is_external__notin": ["true,false"]}
        )
        internal = Covid.objects.exclude(is_external__in=[True, False])
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/",
            data={
                "is_external__notin": [
                    "true,false",
                    "True,false",
                ]
            },
        )
        internal = Covid.objects.exclude(is_external__in=[True, False]).exclude(
            is_external__in=[True, False]
        )
        self.assertEqualCids(results, internal)

    def test_boolean_field_range(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"is_external__range": ["true,false"]}
        )
        internal = Covid.objects.filter(is_external__range=[True, False])
        self.assertEqualCids(results, internal)

    def test_boolean_field_isnull(self):
        results = self.client_get_paginated(
            "/data/covid/", data={"is_external__isnull": ["true"]}
        )
        internal = Covid.objects.filter(is_external__isnull=True)
        self.assertEqualCids(results, internal)

        results = self.client_get_paginated(
            "/data/covid/", data={"is_external__isnull": ["false"]}
        )
        internal = Covid.objects.filter(is_external__isnull=False)
        self.assertEqualCids(results, internal)

    def test_boolean_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            results = self.client_get_paginated(
                "/data/covid/", data={f"is_external__{lookup}": ["false"]}
            )
            internal = Covid.objects.filter(**{f"is_external__{lookup}": False})
            self.assertEqualCids(results, internal)

    def test_boolean_field_non_boolean(self):
        for value in [
            "tru mayn",
            "fr fr",
            "nah",
            "cap",
            "no cap",
            "falseee",
            "101011111000",
            "1",
            "0",
            1,
            0,
            "tRUE",
            "fAlSe",
        ]:
            # Exact
            results = self.client_get_paginated(
                "/data/covid/",
                data={"is_external": value},
                expected_status_code=status.HTTP_400_BAD_REQUEST,
            )

            # Base lookups
            for lookup in BASE_LOOKUPS:
                results = self.client_get_paginated(
                    "/data/covid/",
                    data={f"is_external__{lookup}": [value]},
                    expected_status_code=status.HTTP_400_BAD_REQUEST,
                )
