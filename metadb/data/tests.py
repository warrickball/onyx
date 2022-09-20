from rest_framework.test import APITestCase
from rest_framework import status
from .models import Pathogen, Covid, Mpx
from .views import get_pathogen_model, enforce_optional_value_groups, enforce_field_set
from accounts.models import User, Institute
from utils.responses import APIResponse
from .filters import BASE_LOOKUPS, CHAR_LOOKUPS
from django.conf import settings
import secrets
import random
from datetime import date


class TestGetPathogenModel(APITestCase):
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


class METADBTestCase(APITestCase):
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

    def assertEqualCids(self, results, internal):
        self.assertEqual(
            sorted(result["cid"] for result in results),
            sorted(internal.values_list("cid", flat=True)),
        )

    def showEqualCids(self, results, internal):
        return sorted(result["cid"] for result in results) == sorted(
            internal.values_list("cid", flat=True)
        )

    def client_get_paginated(
        self, *args, expected_status_code=status.HTTP_200_OK, **kwargs
    ):
        response = self.client.get(*args, **kwargs)
        self.assertEqual(response.status_code, expected_status_code)

        results = response.json().get("results")
        _next = response.json().get("next")

        while _next is not None:
            response = self.client.get(
                _next,
            )
            self.assertEqual(response.status_code, expected_status_code)
            results.extend(response.json().get("results"))
            _next = response.json().get("next")

        return results


def get_covid_data(institute):
    sender_sample_id = f"S-{secrets.token_hex(3).upper()}"
    run_name = f"R-{'.'.join([str(random.randint(0, 9)) for _ in range(9)])}"
    pathogen_dict = {
        "sender_sample_id": sender_sample_id,
        "run_name": run_name,
        "pathogen_code": "COVID",
        "institute": institute,
        "fasta_path": f"{sender_sample_id}.{run_name}.fasta",
        "bam_path": f"{sender_sample_id}.{run_name}.bam",
        "is_external": random.choice([True, False]),
        "fasta_header": random.choice(["MN908947.3", "NC_045512", "hello", "goodbye"]),
        "sample_type": random.choice(["SWAB", "SERUM"]),
    }
    coin = random.randint(0, 2)
    if coin == 0:
        pathogen_dict[
            "collection_month"
        ] = f"{random.choice(['2021', '2022'])}-{random.randint(1, 12)}"
    elif coin == 1:
        pathogen_dict[
            "received_month"
        ] = f"{random.choice(['2021', '2022'])}-{random.randint(1, 12)}"
    else:
        pathogen_dict[
            "collection_month"
        ] = f"{random.choice(['2021', '2022'])}-{random.randint(1, 12)}"
        pathogen_dict[
            "received_month"
        ] = f"{random.choice(['2021', '2022'])}-{random.randint(1, 12)}"

    return pathogen_dict


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


class TestGetPathogen(METADBTestCase):
    def setUp(self):
        self.institute = Institute.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_approved_user("user", self.institute.code)

        settings.CURSOR_PAGINATION_PAGE_SIZE = 20
        for _ in range(settings.CURSOR_PAGINATION_PAGE_SIZE * 5):
            covid_data = get_covid_data(self.institute)
            Covid.objects.create(**covid_data)

    def test_everything(self):
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

    def test_unauthenticated_get(self):
        self.client.force_authenticate(user=None)  # type: ignore
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authenticated_user(
                "authenticated-user", institute=self.institute.code
            )
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_403_FORBIDDEN
        )

    def test_approved_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_approved_user(
                "approved-user", institute=self.institute.code
            )
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_200_OK
        )

    def test_authority_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_authority_user(
                "authority-user", institute=self.institute.code
            )
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_200_OK
        )

    def test_admin_get(self):
        self.client.force_authenticate(  # type: ignore
            user=self.setup_admin_user("admin-user", institute=self.institute.code)
        )
        results = self.client_get_paginated(
            "/data/covid/", expected_status_code=status.HTTP_200_OK
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
