from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, Site
from accounts.views import create_username


class TestCreateUser(APITestCase):
    def setUp(self):
        self.site = Site.objects.create(
            code="stuff", name="Department of Important Stuff"
        )

    def test_create_user(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=username).exists())

    def test_create_user_preexisting_user(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=username).exists())

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(username=username).count(), 1)

    def test_create_user_preexisting_user_case_insensitive(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=username).exists())

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name.upper(),
                "last_name": last_name.upper(),
                "password": "pass123456",
                "email": "test@tom.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(username=username).count(), 1)
        self.assertEqual(
            User.objects.get(username=username),
            User.objects.get(username=username.upper()),
        )

    def test_create_user_preexisting_email(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=username).exists())

        first_name = "jerry"

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(email="tom@test.com").count(), 1)

    def test_create_user_preexisting_email_case_insensitive(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=username).exists())

        first_name = "jerry"

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "tom@test.com".upper(),
                "site": self.site.code,
            },
        )
        self.assertEqual(User.objects.filter(email="tom@test.com").count(), 1)
        self.assertEqual(
            User.objects.get(email="tom@test.com"),
            User.objects.get(email="tom@test.com".upper()),
        )

    def test_create_user_invalid_email(self):
        for (first_name, last_name), email in [
            (("test", "tom"), "tomtestcom"),
            (("test", "jerry"), "jerrytest.com"),
            (("test", "sid"), "sid@test"),
        ]:
            username = create_username(first_name, last_name)

            response = self.client.post(
                "/accounts/register/",
                data={
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": "pass123456",
                    "email": email,
                    "site": self.site.code,
                },
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=username).exists())

    def test_create_user_invalid_site(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        response = self.client.post(
            "/accounts/register/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "password": "pass123456",
                "email": "jerry@test.com",
                "site": "NOTAPLACE",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username=username).exists())

    def test_create_user_fields_missing(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "password": "pass123456",
            "email": "jerry@test.com",
            "site": self.site.code,
        }
        for i, key in enumerate(data):
            data_ = dict(data)
            data_["last_name"] += "abcde"[i]
            data_["email"] = data_["last_name"] + "@test.com"
            username = create_username(data_["first_name"], data_["last_name"])
            data_.pop(key)

            response = self.client.post(
                "/accounts/register/",
                data=data_,
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=username).exists())

    def test_create_user_bad_password(self):
        first_name = "tom"
        last_name = "test"
        username = create_username(first_name, last_name)

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "site": self.site.code,
        }
        # According to django... bad passwords are:
        # Less than 8 characters
        # Not entirely numbers
        # Not match username too closely
        # Not on list of 20000 most common passwords
        for i, bad_pass in enumerate(
            ["hi", "123456789", username, "123abc", ".......", "password"]
        ):
            data_ = dict(data)
            data_["last_name"] += "abcdef"[i]
            data_["email"] = data_["last_name"] + "@test.com"
            data_["password"] = bad_pass
            username = create_username(data_["first_name"], data_["last_name"])

            response = self.client.post(
                "/accounts/register/",
                data=data_,
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=username).exists())
