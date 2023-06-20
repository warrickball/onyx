from django.core.management import call_command
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, Site
import os


directory = os.path.dirname(os.path.abspath(__file__))


class OnyxTestCase(APITestCase):
    def setUp(self):
        # Set up test project, choices, and site
        call_command(
            "project",
            "test",
            content_type="data.testmodel",
            groups=os.path.join(directory, "groups.txt"),
            quiet=True,
        )
        call_command(
            "choices",
            os.path.join(directory, "choices.txt"),
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
