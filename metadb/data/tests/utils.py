from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
import secrets
import random


class METADBTestCase(APITestCase):
    def setup_authenticated_user(self, username, site):
        first_name = username[-1]
        last_name = username[0:-1]
        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "site": site,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        self.client.force_authenticate(user)  # type: ignore
        return user

    def setup_approved_user(self, username, site):
        first_name = username[-1]
        last_name = username[0:-1]
        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "site": site,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        user.is_site_approved = True
        self.client.force_authenticate(user)  # type: ignore
        return user

    def setup_authority_user(self, username, site):
        first_name = username[-1]
        last_name = username[0:-1]
        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "site": site,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        user.is_site_approved = True
        user.is_site_authority = True
        self.client.force_authenticate(user)  # type: ignore
        return user

    def setup_admin_user(self, username, site):
        first_name = username[-1]
        last_name = username[0:-1]
        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "site": site,
            },
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


def get_covid_data(site):
    sample_id = f"S-{secrets.token_hex(3).upper()}"
    run_name = f"R-{'.'.join([str(random.randint(0, 9)) for _ in range(9)])}"
    pathogen_dict = {
        "sample_id": sample_id,
        "run_name": run_name,
        "pathogen_code": "COVID",
        "site": site,
        "fasta_path": f"{sample_id}.{run_name}.fasta",
        "bam_path": f"{sample_id}.{run_name}.bam",
        "received_month": f"{random.choice(['2020', '2021'])}-{random.randint(1, 12)}",
    }
    return pathogen_dict
