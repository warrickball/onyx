from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
import secrets
import random


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
