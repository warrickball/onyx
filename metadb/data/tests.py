from rest_framework.test import APITestCase
from rest_framework import status
from .models import Pathogen, Covid, Mpx
from .views import get_pathogen_model, enforce_optional_value_groups, enforce_field_set
from accounts.models import User, Institute
from utils.responses import APIResponse
from .filters import BASE_LOOKUPS, CHAR_LOOKUPS
import secrets
import random
from datetime import date


class TestGetPathogenModel(APITestCase):
    def setUp(self):
        pass

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


class CustomAPITestCase(APITestCase):
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

    def assertEqualCids(self, response, internal):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(result["cid"] for result in response.json()["results"]),
            set(internal.values_list("cid", flat=True)),
        )

    def showEqualCids(self, response, internal):
        return set(result["cid"] for result in response.json()["results"]) == set(
            internal.values_list("cid", flat=True)
        )


def get_covid_data(institute):
    sender_sample_id = f"S-{secrets.token_hex(3).upper()}"
    run_name = f"R-{random.randint(1, 100)}"
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


class TestGetPathogen(CustomAPITestCase):
    def setUp(self):
        self.institute = Institute.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )
        self.user = self.setup_approved_user("user", self.institute.code)

        for _ in range(100):
            covid_data = get_covid_data(self.institute)
            Covid.objects.create(**covid_data)


class TestGetPathogenChoiceField(TestGetPathogen):
    def test_choice_field_exact(self):
        for value in ["SWAB", "SERUM"]:
            response = self.client.get("/data/covid/", data={"sample_type": value})
            internal = Covid.objects.filter(sample_type=value)
            self.assertEqualCids(response, internal)

    def test_choice_field_in(self):
        response = self.client.get(
            "/data/covid/", data={"sample_type__in": ["SWAB,SERUM"]}
        )
        internal = Covid.objects.filter(sample_type__in=["SWAB", "SERUM"])
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/",
            data={"sample_type__in": ["SWAB,SERUM", "SWAB"]},
        )
        internal = Covid.objects.filter(sample_type__in=["SWAB", "SERUM"]).filter(
            sample_type__in=["SWAB"]
        )
        self.assertEqualCids(response, internal)

    def test_choice_field_notin(self):
        response = self.client.get(
            "/data/covid/", data={"sample_type__notin": ["SWAB,SERUM"]}
        )
        internal = Covid.objects.exclude(sample_type__in=["SWAB", "SERUM"])
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/",
            data={"sample_type__notin": ["SWAB", "SERUM"]},
        )
        internal = Covid.objects.exclude(sample_type__in=["SWAB"]).exclude(
            sample_type__in=["SERUM"]
        )
        self.assertEqualCids(response, internal)

    def test_choice_field_range(self):
        response = self.client.get(
            "/data/covid/", data={"sample_type__range": ["SERUM,SWAB"]}
        )
        internal = Covid.objects.filter(sample_type__range=["SERUM", "SWAB"])
        self.assertEqualCids(response, internal)

    def test_choice_field_isnull(self):
        response = self.client.get(
            "/data/covid/", data={"sample_type__isnull": ["true"]}
        )
        internal = Covid.objects.filter(sample_type__isnull=True)
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/", data={"sample_type__isnull": ["false"]}
        )
        internal = Covid.objects.filter(sample_type__isnull=False)
        self.assertEqualCids(response, internal)

    def test_choice_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            response = self.client.get(
                "/data/covid/", data={f"sample_type__{lookup}": ["SWAB"]}
            )
            internal = Covid.objects.filter(**{f"sample_type__{lookup}": "SWAB"})
            self.assertEqualCids(response, internal)

    def test_choice_field_char_lookups(self):
        for lookup in CHAR_LOOKUPS:
            response = self.client.get(
                "/data/covid/", data={f"sample_type__{lookup}": ["SWAB"]}
            )
            internal = Covid.objects.filter(**{f"sample_type__{lookup}": "SWAB"})
            self.assertEqualCids(response, internal)


class TestGetPathogenCharField(TestGetPathogen):
    def test_char_field_exact(self):
        for value in ["MN908947.3", "NC_045512", "hello", "goodbye"]:
            response = self.client.get("/data/covid/", data={"fasta_header": value})
            internal = Covid.objects.filter(fasta_header=value)
            self.assertEqualCids(response, internal)

    def test_char_field_in(self):
        response = self.client.get(
            "/data/covid/", data={"fasta_header__in": ["NC_045512,hello"]}
        )
        internal = Covid.objects.filter(fasta_header__in=["NC_045512", "hello"])
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/",
            data={"fasta_header__in": ["NC_045512,hello", "MN908947.3,hello"]},
        )
        internal = Covid.objects.filter(fasta_header__in=["NC_045512", "hello"]).filter(
            fasta_header__in=["MN908947.3", "hello"]
        )
        self.assertEqualCids(response, internal)

    def test_char_field_notin(self):
        response = self.client.get(
            "/data/covid/", data={"fasta_header__notin": ["NC_045512,hello"]}
        )
        internal = Covid.objects.exclude(fasta_header__in=["NC_045512", "hello"])
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/",
            data={"fasta_header__notin": ["NC_045512,hello", "MN908947.3,hello"]},
        )
        internal = Covid.objects.exclude(
            fasta_header__in=["NC_045512", "hello"]
        ).exclude(fasta_header__in=["MN908947.3", "hello"])
        self.assertEqualCids(response, internal)

    def test_char_field_range(self):
        response = self.client.get(
            "/data/covid/", data={"fasta_header__range": ["goodbye,hello"]}
        )
        internal = Covid.objects.filter(fasta_header__range=["goodbye", "hello"])
        self.assertEqualCids(response, internal)

    def test_char_field_isnull(self):
        response = self.client.get(
            "/data/covid/", data={"fasta_header__isnull": ["true"]}
        )
        internal = Covid.objects.filter(fasta_header__isnull=True)
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/", data={"fasta_header__isnull": ["false"]}
        )
        internal = Covid.objects.filter(fasta_header__isnull=False)
        self.assertEqualCids(response, internal)

    def test_char_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            response = self.client.get(
                "/data/covid/", data={f"fasta_header__{lookup}": ["hello"]}
            )
            internal = Covid.objects.filter(**{f"fasta_header__{lookup}": "hello"})
            self.assertEqualCids(response, internal)

    def test_char_field_char_lookups(self):
        for lookup in CHAR_LOOKUPS:
            response = self.client.get(
                "/data/covid/", data={f"fasta_header__{lookup}": ["hello"]}
            )
            internal = Covid.objects.filter(**{f"fasta_header__{lookup}": "hello"})
            self.assertEqualCids(response, internal)


class TestGetPathogenYearMonthField(TestGetPathogen):
    def test_yearmonth_field_exact(self):
        for value in ["2021-03", "2022-01", "2022-04", "2022-12"]:
            response = self.client.get("/data/covid/", data={"collection_month": value})
            internal = Covid.objects.filter(collection_month=value)
            self.assertEqualCids(response, internal)

    def test_yearmonth_field_in(self):
        response = self.client.get(
            "/data/covid/", data={"collection_month__in": ["2021-03,2022-04"]}
        )
        internal = Covid.objects.filter(collection_month__in=["2021-03", "2022-04"])
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/",
            data={"collection_month__in": ["2021-03,2022-04", "2022-01,2022-04"]},
        )
        internal = Covid.objects.filter(
            collection_month__in=["2021-03", "2022-04"]
        ).filter(collection_month__in=["2022-01", "2022-04"])
        self.assertEqualCids(response, internal)

    def test_yearmonth_field_notin(self):
        response = self.client.get(
            "/data/covid/", data={"collection_month__notin": ["2021-03,2022-04"]}
        )
        internal = Covid.objects.exclude(collection_month__in=["2021-03", "2022-04"])
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/",
            data={"collection_month__notin": ["2021-03,2022-04", "2022-01,2022-04"]},
        )
        internal = Covid.objects.exclude(
            collection_month__in=["2021-03", "2022-04"]
        ).exclude(collection_month__in=["2022-01", "2022-04"])
        self.assertEqualCids(response, internal)

    def test_yearmonth_field_range(self):
        response = self.client.get(
            "/data/covid/", data={"collection_month__range": ["2021-03,2022-04"]}
        )
        internal = Covid.objects.filter(collection_month__range=["2021-03", "2022-04"])
        self.assertEqualCids(response, internal)

    def test_yearmonth_field_isnull(self):
        response = self.client.get(
            "/data/covid/", data={"collection_month__isnull": ["true"]}
        )
        internal = Covid.objects.filter(collection_month__isnull=True)
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/", data={"collection_month__isnull": ["false"]}
        )
        internal = Covid.objects.filter(collection_month__isnull=False)
        self.assertEqualCids(response, internal)

    def test_yearmonth_field_iso_year(self):
        response = self.client.get(
            "/data/covid/", data={"collection_month__iso_year": ["2022"]}
        )
        internal = Covid.objects.filter(collection_month__iso_year=2022)
        self.assertEqualCids(response, internal)

    def test_yearmonth_field_iso_year_in(self):
        response = self.client.get(
            "/data/covid/", data={"collection_month__iso_year__in": ["2021,2022"]}
        )
        internal = Covid.objects.filter(collection_month__iso_year__in=[2021, 2022])
        self.assertEqualCids(response, internal)

    def test_yearmonth_field_iso_year_range(self):
        response = self.client.get(
            "/data/covid/", data={"collection_month__iso_year__range": ["2021,2022"]}
        )
        internal = Covid.objects.filter(collection_month__iso_year__range=[2021, 2022])
        self.assertEqualCids(response, internal)

    def test_yearmonth_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            response = self.client.get(
                "/data/covid/", data={f"collection_month__{lookup}": ["2022-04"]}
            )
            internal = Covid.objects.filter(
                **{f"collection_month__{lookup}": "2022-04"}
            )
            self.assertEqualCids(response, internal)


class TestGetPathogenDateField(TestGetPathogen):
    def setUp(self):
        super().setUp()
        today = date.today()
        year, week, day = today.isocalendar()
        self.today = str(today)
        self.today_week = week

    def test_date_field_exact(self):
        for value in ["2021-03-04", "2022-01-01", self.today, "2022-12-25"]:
            response = self.client.get("/data/covid/", data={"published_date": value})
            internal = Covid.objects.filter(published_date=value)
            self.assertEqualCids(response, internal)

    def test_date_field_in(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__in": [f"2021-03-04,{self.today}"]}
        )
        internal = Covid.objects.filter(published_date__in=["2021-03-04", self.today])
        self.assertEqualCids(response, internal)

        response = self.client.get(
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
        self.assertEqualCids(response, internal)

    def test_date_field_notin(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__notin": [f"2021-03-04,{self.today}"]}
        )
        internal = Covid.objects.exclude(published_date__in=["2021-03-04", self.today])
        self.assertEqualCids(response, internal)

        response = self.client.get(
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
        self.assertEqualCids(response, internal)

    def test_date_field_range(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__range": [f"2021-03-04,{self.today}"]}
        )
        internal = Covid.objects.filter(
            published_date__range=["2021-03-04", self.today]
        )
        self.assertEqualCids(response, internal)

    def test_date_field_isnull(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__isnull": ["true"]}
        )
        internal = Covid.objects.filter(published_date__isnull=True)
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/", data={"published_date__isnull": ["false"]}
        )
        internal = Covid.objects.filter(published_date__isnull=False)
        self.assertEqualCids(response, internal)

    def test_date_field_iso_year(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__iso_year": ["2022"]}
        )
        internal = Covid.objects.filter(published_date__iso_year=2022)
        self.assertEqualCids(response, internal)

    def test_date_field_iso_year_in(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__iso_year__in": ["2021,2022"]}
        )
        internal = Covid.objects.filter(published_date__iso_year__in=[2021, 2022])
        self.assertEqualCids(response, internal)

    def test_date_field_iso_year_range(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__iso_year__range": ["2021,2022"]}
        )
        internal = Covid.objects.filter(published_date__iso_year__range=[2021, 2022])
        self.assertEqualCids(response, internal)

    def test_date_field_iso_week(self):
        response = self.client.get(
            "/data/covid/", data={"published_date__iso_week": [str(self.today_week)]}
        )
        internal = Covid.objects.filter(published_date__week=self.today_week)
        self.assertEqualCids(response, internal)

    def test_date_field_iso_week_in(self):
        response = self.client.get(
            "/data/covid/",
            data={"published_date__iso_week__in": [f"{str(self.today_week)},11"]},
        )
        internal = Covid.objects.filter(published_date__week__in=[self.today_week, 11])
        self.assertEqualCids(response, internal)

    def test_date_field_iso_week_range(self):
        response = self.client.get(
            "/data/covid/",
            data={"published_date__iso_week__range": [f"11,{str(self.today_week)}"]},
        )
        internal = Covid.objects.filter(
            published_date__week__range=[11, self.today_week]
        )
        self.assertEqualCids(response, internal)

    def test_date_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            response = self.client.get(
                "/data/covid/", data={f"published_date__{lookup}": [self.today]}
            )
            internal = Covid.objects.filter(**{f"published_date__{lookup}": self.today})
            self.assertEqualCids(response, internal)


class TestGetPathogenBooleanField(TestGetPathogen):
    def test_boolean_field(self):
        for value in ["true", "True"]:
            response = self.client.get("/data/covid/", data={"is_external": value})
            internal = Covid.objects.filter(is_external=True)
            self.assertEqualCids(response, internal)

        for value in ["false", "False"]:
            response = self.client.get("/data/covid/", data={"is_external": value})
            internal = Covid.objects.filter(is_external=False)
            self.assertEqualCids(response, internal)

    def test_boolean_field_in(self):
        response = self.client.get(
            "/data/covid/", data={"is_external__in": ["true,false"]}
        )
        internal = Covid.objects.filter(is_external__in=[True, False])
        self.assertEqualCids(response, internal)

        response = self.client.get(
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
        self.assertEqualCids(response, internal)

    def test_boolean_field_notin(self):
        response = self.client.get(
            "/data/covid/", data={"is_external__notin": ["true,false"]}
        )
        internal = Covid.objects.exclude(is_external__in=[True, False])
        self.assertEqualCids(response, internal)

        response = self.client.get(
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
        self.assertEqualCids(response, internal)

    def test_boolean_field_range(self):
        response = self.client.get(
            "/data/covid/", data={"is_external__range": ["true,false"]}
        )
        internal = Covid.objects.filter(is_external__range=[True, False])
        self.assertEqualCids(response, internal)

    def test_boolean_field_isnull(self):
        response = self.client.get(
            "/data/covid/", data={"is_external__isnull": ["true"]}
        )
        internal = Covid.objects.filter(is_external__isnull=True)
        self.assertEqualCids(response, internal)

        response = self.client.get(
            "/data/covid/", data={"is_external__isnull": ["false"]}
        )
        internal = Covid.objects.filter(is_external__isnull=False)
        self.assertEqualCids(response, internal)

    def test_boolean_field_base_lookups(self):
        for lookup in BASE_LOOKUPS:
            response = self.client.get(
                "/data/covid/", data={f"is_external__{lookup}": ["false"]}
            )
            internal = Covid.objects.filter(**{f"is_external__{lookup}": False})
            self.assertEqualCids(response, internal)
