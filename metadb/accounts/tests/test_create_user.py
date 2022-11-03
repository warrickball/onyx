from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, Site


class TestCreateUser(APITestCase):
    def setUp(self):
        self.site = Site.objects.create(
            code="DEPTSTUFF", name="Department of Important Stuff"
        )

    def test_create_user(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-tom",
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="test-tom").exists())

    def test_create_user_preexisting_user(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-tom",
                "password": "pass123456",
                "email": "jerry@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="test-tom").exists())

        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-tom",
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(username="test-tom").count(), 1)

    def test_create_user_preexisting_user_case_insensitive(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-tom",
                "password": "pass123456",
                "email": "jerry@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="test-tom").exists())

        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "TeSt-ToM",
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(username="test-tom").count(), 1)
        self.assertEqual(
            User.objects.get(username="test-tom"), User.objects.get(username="TeSt-ToM")
        )

    def test_create_user_preexisting_email(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-tom",
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="test-tom").exists())

        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-jerry",
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(email="tom@test.com").count(), 1)

    def test_create_user_preexisting_email_case_insensitive(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-tom",
                "password": "pass123456",
                "email": "tom@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="test-tom").exists())

        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-jerry",
                "password": "pass123456",
                "email": "ToM@test.com",
                "site": self.site.code,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(email="tom@test.com").count(), 1)
        self.assertEqual(
            User.objects.get(email="tom@test.com"),
            User.objects.get(email="ToM@test.com"),
        )

    def test_create_user_invalid_email(self):
        for user, email in [
            ("test-tom", "tomtestcom"),
            ("test-jerry", "jerrytest.com"),
            ("test-sid", "sid@test"),
        ]:
            response = self.client.post(
                "/accounts/register/",
                data={
                    "username": user,
                    "password": "pass123456",
                    "email": email,
                    "site": self.site.code,
                },
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=user).exists())

    def test_create_user_invalid_site(self):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username": "test-jerry",
                "password": "pass123456",
                "email": "jerry@test.com",
                "site": "NOTAPLACE",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="test-jerry").exists())

    def test_create_user_fields_missing(self):
        data = {
            "username": "test-jerry",
            "password": "pass123456",
            "email": "jerry@test.com",
            "site": self.site.code,
        }
        for i, key in enumerate(data):
            data_ = dict(data)
            data_["username"] += str(i)
            data_["email"] = data_["username"] + "@test.com"
            username = data_["username"]
            data_.pop(key)

            response = self.client.post(
                "/accounts/register/",
                data=data_,
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=username).exists())

    def test_create_user_bad_password(self):
        data = {
            "username": "jerrymeister",
            "site": self.site.code,
        }
        # According to django... bad passwords are:
        # Less than 8 characters
        # Not entirely numbers
        # Not match username too closely
        # Not on list of 20000 most common passwords
        for i, bad_pass in enumerate(
            ["hi", "123456789", "jerrymeister", "123abc", ".......", "password"]
        ):
            data_ = dict(data)
            data_["username"] += str(i)
            data_["email"] = data_["username"] + "@test.com"
            data_["password"] = bad_pass
            username = data_["username"]

            response = self.client.post(
                "/accounts/register/",
                data=data_,
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.filter(username=username).exists())
