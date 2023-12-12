import copy
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.serializers import BooleanField
from ..utils import OnyxTestCase, _test_record
from ...models.projects.test import TestModel, TestModelRecord


default_payload = {
    "sample_id": "sample-1234",
    "run_name": "run-5678",
    "collection_month": "2023-01",
    "received_month": "2023-02",
    "text_option_1": "hi",
    "text_option_2": "bye",
    "submission_date": "2023-03-01",
    "country": "eng",
    "region": "nw",
    "concern": False,
    "tests": 2,
    "score": 42.832,
    "start": 1,
    "end": 2,
    "records": [
        {
            "test_id": 1,
            "test_pass": True,
            "test_start": "2023-01",
            "test_end": "2023-02",
            "score_a": 42.101,
        },
        {
            "test_id": 2,
            "test_pass": False,
            "test_start": "2023-03",
            "test_end": "2023-04",
            "score_b": 45.010,
        },
    ],
}

bad_yearmonths = {
    "0-0-0-0-",
    "0000-01",
    "209999999999-01",
    "2023-01-01",
    "2023-0",
}

bad_dates = {
    "0-0-0-0-",
    "0000-01",
    "209999999999-01-01",
    "2023-01",
}

# (submitted, coerced) format
good_choices = {
    ("nW", "nw"),
    ("Nw", "nw"),
    ("NW", "nw"),
    (" nw", "nw"),
    ("    ", ""),
}

bad_choices = [
    "not a choice",
]

# (submitted, coerced) format
good_bools = [(value, True) for value in BooleanField.TRUE_VALUES] + [
    (value, False) for value in BooleanField.FALSE_VALUES
]

bad_bools = [
    "tRUE",
    "truE",
    " True ",
    "  False   ",
    "fALSE",
    "FalsE",
]

# (submitted, coerced) format
good_ints = [
    ("5", 5),
    ("  7  ", 7),
    ("1.", 1),
]

bad_ints = [
    "2.45",
    "hello",
]

good_floats = [
    ("42.832", 42.832),
    (" 55.873 ", 55.873),
]

bad_floats = [
    "2.45.3",
    "1/0",
    "goodbye",
]


class TestCreateView(OnyxTestCase):
    def setUp(self):
        """
        Create a user with the required permissions.
        """

        super().setUp()
        self.endpoint = reverse("data.project", kwargs={"code": "test"})
        self.user = self.setup_user(
            "testuser", roles=["is_staff"], groups=["test.add.base"]
        )

    def test_basic_ok(self):
        """
        Test that a basic payload works.
        """

        payload = copy.deepcopy(default_payload)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        assert TestModelRecord.objects.count() == 2
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance, created=True)

    def test_nullables_ok(self):
        """
        Test that a payload with nullables works.
        """

        payload = copy.deepcopy(default_payload)
        payload.pop("collection_month")
        payload.pop("region")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        assert TestModelRecord.objects.count() == 2
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance, created=True)

    def test_unpermissioned_viewable_field_fail(self):
        """
        Test that a payload with a viewable field that the user does not have
        permission to create fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["cid"] = "helloooo"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_unpermissioned_unviewable_field_fail(self):
        """
        Test that a payload with an unviewable field that the user does not
        have permission to create fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["suppressed"] = "helloooo"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_unknown_fields_fail(self):
        """
        Test that a payload with unknown fields fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["hello"] = "hi"
        payload["goodbye"] = "bye"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_required_fields_fail(self):
        """
        Test that a payload with missing required fields fails.
        """

        payload = copy.deepcopy(default_payload)
        payload.pop("sample_id")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_required_fields_fail(self):
        """
        Test that a payload with missing required nested fields fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["records"][0].pop("test_id")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_conditional_required_fields_fail(self):
        """
        Test that a payload with missing conditionally required fields fails.
        """

        payload = copy.deepcopy(default_payload)
        payload.pop("country")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_conditional_required_fields_fail(self):
        """
        Test that a payload with missing conditionally required nested fields
        fails.
        """

        # We do not have all requirements for score_c
        # score_c requires score_a and score_b
        payload = copy.deepcopy(default_payload)
        payload["records"][0]["score_c"] = 42.3
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_conditional_required_fields_ok(self):
        """
        Test that a payload with missing conditionally required nested fields
        works.
        """

        # We have all requirements for score_c
        payload = copy.deepcopy(default_payload)
        payload["records"][0]["score_a"] = 42.3
        payload["records"][0]["score_b"] = 42.3112
        payload["records"][0]["score_c"] = 42.4242
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        assert TestModelRecord.objects.count() == 2
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance, created=True)

    def test_unique_together(self):
        """
        Test that a payload with a unique together constraint works.
        """

        # TODO: Split out unique_together tests into ok and fail

        payload = copy.deepcopy(default_payload)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        assert TestModelRecord.objects.count() == 2
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance, created=True)

        payload = copy.deepcopy(default_payload)
        payload["sample_id"] = "sample-2345"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 2
        assert TestModelRecord.objects.count() == 4
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance, created=True)

        payload = copy.deepcopy(default_payload)
        payload["run_name"] = "run-2"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 3
        assert TestModelRecord.objects.count() == 6
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance, created=True)

        payload = copy.deepcopy(default_payload)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 3
        assert TestModelRecord.objects.count() == 6
        assert (
            TestModel.objects.filter(sample_id=default_payload["sample_id"]).count()
            == 2
        )
        assert (
            TestModel.objects.filter(run_name=default_payload["run_name"]).count() == 2
        )

    def test_nested_unique_together_fail(self):
        """
        Test that a payload which violates a nested unique together constraint fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["records"][0]["test_id"] = payload["records"][1]["test_id"]
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_optional_value_group_fail(self):
        """
        Test that a payload which violates an optional value group constraint fails.
        """

        payload = copy.deepcopy(default_payload)
        payload.pop("collection_month")
        payload.pop("received_month")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

        for op_1, op_2 in [
            ("collection_month", "received_month"),
            ("text_option_1", "text_option_2"),
        ]:
            for empty_value in [" ", "", None]:
                payload = copy.deepcopy(default_payload)
                payload[op_1] = empty_value
                payload[op_2] = empty_value
                response = self.client.post(self.endpoint, data=payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                assert TestModel.objects.count() == 0
                assert TestModelRecord.objects.count() == 0

    def test_nested_optional_value_group_fail(self):
        """
        Test that a payload which violates a nested optional value group constraint fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["records"][0].pop("score_a", None)
        payload["records"][0].pop("score_b", None)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_ordering_fail(self):
        """
        Test that a payload which violates an ordering constraint fails.
        """

        # Testing ordering with yearmonths
        payload = copy.deepcopy(default_payload)
        payload["collection_month"] = "2023-02"
        payload["received_month"] = "2023-01"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

        # Testing ordering with integers
        payload = copy.deepcopy(default_payload)
        start = payload.pop("start")
        end = payload.pop("end")
        payload["end"] = start
        payload["start"] = end
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_ordering_fail(self):
        """
        Test that a payload which violates a nested ordering constraint fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["records"][1]["test_start"] = "2023-04"
        payload["records"][1]["test_end"] = "2023-03"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_charfield_too_long_fail(self):
        """
        Test that a payload which violates a CharField length constraint fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["sample_id"] = "A" * 1000 + "H"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_bad_yearmonth_fail(self):
        """
        Test that a payload with invalid date (YYYY-MM) values fails.
        """

        for bad_yearmonth in bad_yearmonths:
            payload = copy.deepcopy(default_payload)
            payload["collection_month"] = bad_yearmonth
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_future_yearmonth_fail(self):
        """
        Test that a payload with date (YYYY-MM) values in the future fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["collection_month"] = (datetime.today() + timedelta(days=60)).strftime(
            "%Y-%m"
        )
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_bad_date_fail(self):
        """
        Test that a payload with invalid date (YYYY-MM-DD) values fails.
        """

        for bad_date in bad_dates:
            payload = copy.deepcopy(default_payload)
            payload["submission_date"] = bad_date
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_future_date_fail(self):
        """
        Test that a payload with date (YYYY-MM-DD) values in the future fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["submission_date"] = (datetime.today() + timedelta(days=60)).strftime(
            "%Y-%m-%d"
        )
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_good_choice_ok(self):
        """
        Test that a payload with valid choices works.
        """

        for good_choice, expected in good_choices:
            payload = copy.deepcopy(default_payload)
            payload["region"] = good_choice
            response = self.client.post(self.endpoint, data=payload)
            payload["region"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance, created=True)
            TestModel.objects.all().delete()

    def test_bad_choice_fail(self):
        """
        Test that a payload with invalid choices fails.
        """

        for bad_choice in bad_choices:
            payload = copy.deepcopy(default_payload)
            payload["region"] = bad_choice
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_choice_constraint_fail(self):
        """
        Test that a payload which violates a choice constraint fails.
        """

        payload = copy.deepcopy(default_payload)
        payload["country"] = "wales"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

        payload = copy.deepcopy(default_payload)
        payload["region"] = "other"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_good_bool_ok(self):
        """
        Test that a payload with valid booleans works.
        """

        for good_bool, expected in good_bools:
            payload = copy.deepcopy(default_payload)
            payload["concern"] = good_bool
            response = self.client.post(self.endpoint, data=payload)
            payload["concern"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance, created=True)
            TestModel.objects.all().delete()

    def test_bad_bool_fail(self):
        """
        Test that a payload with invalid booleans fails.
        """

        for bad_bool in bad_bools:
            payload = copy.deepcopy(default_payload)
            payload["concern"] = bad_bool
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_good_int_ok(self):
        """
        Test that a payload with valid integers works.
        """

        for good_int, expected in good_ints:
            payload = copy.deepcopy(default_payload)
            payload["tests"] = good_int
            response = self.client.post(self.endpoint, data=payload)
            payload["tests"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance, created=True)
            TestModel.objects.all().delete()

    def test_bad_int_fail(self):
        """
        Test that a payload with invalid integers fails.
        """

        for bad_int in bad_ints:
            payload = copy.deepcopy(default_payload)
            payload["tests"] = bad_int
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_good_float_ok(self):
        """
        Test that a payload with valid floats works.
        """

        for good_float, expected in good_floats:
            payload = copy.deepcopy(default_payload)
            payload["score"] = good_float
            response = self.client.post(self.endpoint, data=payload)
            payload["score"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance, created=True)
            TestModel.objects.all().delete()

    def test_bad_float_fail(self):
        """
        Test that a payload with invalid floats fails.
        """

        for bad_float in bad_floats:
            payload = copy.deepcopy(default_payload)
            payload["score"] = bad_float
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_empty_request_fail(self):
        """
        Test that an empty payload fails.
        """

        for payload in [None, {}]:
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_bad_request_fail(self):
        """
        Test that a badly structured payload fails.
        """

        for payload in [
            "",
            "hi",
            0,
            [],
            {"records": ""},
            {"records": "hi"},
            {"records": 0},
            {"records": {}},
            {"sample_id": []},
            {None: {}},
        ]:
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0
