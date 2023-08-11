import os
import random
import logging
from django.core.management import call_command
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, Site


directory = os.path.dirname(os.path.abspath(__file__))


class OnyxTestCase(APITestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

        # Set up test project, choices, and site
        call_command(
            "project",
            os.path.join(directory, "project.json"),
            quiet=True,
        )
        call_command(
            "choices",
            os.path.join(directory, "choices.json"),
            quiet=True,
        )
        call_command(
            "choiceconstraints",
            os.path.join(directory, "constraints.json"),
            quiet=True,
        )
        self.site = Site.objects.create(
            code="TEST",
            description="Department of Testing",
        )

    def setup_user(self, username, roles=None, groups=None):
        first_name = username[-1]
        last_name = username[0:-1]
        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": f"{username}@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)

        if roles:
            for role in roles:
                setattr(user, role, True)

        if groups:
            for group in groups:
                g = Group.objects.get(name=group)
                user.groups.add(g)

        self.client.force_authenticate(user)  # type: ignore
        return user


def test_data(n=100):
    data = []
    for i in range(n):
        country_region_group = random.randint(0, 4)
        records = random.randint(0, 1)
        x = {
            "sample_id": f"sample-{i}",
            "run_name": f"run-{random.randint(1, 3)}",
            "collection_month": f"2022-{random.randint(1, 12)}",
            "received_month": f"2023-{random.randint(1, 6)}",
            "submission_date": f"2023-{random.randint(1, 6)}-{random.randint(1, 25)}",
            "country": ["eng", "scot", "wales", "ni", ""][country_region_group],
            "region": [
                random.choice(["ne", "se", "nw", "sw", ""]),
                "other",
                "other",
                "other",
                "",
            ][country_region_group],
            "concern": random.choice([True, False]),
            "tests": 2,
            "score": random.random() * 42,
            "start": random.randint(1, 5),
            "end": random.randint(6, 10),
        }
        if records:
            x["records"] = [
                {
                    "test_id": 1,
                    "test_pass": random.choice([True, False]),
                    "test_start": f"2022-{random.randint(1, 12)}",
                    "test_end": f"2023-{random.randint(1, 6)}",
                    "score_a": random.random() * 42,
                },
                {
                    "test_id": 2,
                    "test_pass": random.choice([True, False]),
                    "test_start": f"2022-{random.randint(1, 12)}",
                    "test_end": f"2023-{random.randint(1, 6)}",
                    "score_b": random.random() * 42,
                },
            ]
        data.append(x)
    return data
