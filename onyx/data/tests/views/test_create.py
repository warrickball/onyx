import copy
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.reverse import reverse
from ..utils import OnyxTestCase
from ...models.projects.test import TestModel, TestModelRecord


default_payload = {
    "sample_id": "sample-1234",
    "run_name": "run-1",
    "collection_month": "2023-01",
    "received_month": "2023-02",
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

bad_yearmonths = [
    "0-0-0-0-",
    "0000-01",
    "209999999999-01",
    "2023-01-01",
    "2023-0",
]

bad_dates = [
    "0-0-0-0-",
    "0000-01",
    "209999999999-01-01",
    "2023-01",
]

good_choices = [
    ("nW", "nw"),
    ("Nw", "nw"),
    ("NW", "nw"),
]

bad_choices = [
    "nws",
    "  nw",
    " ",
]

good_bools = [
    ("true", True),
    ("True", True),
    ("TRUE", True),
    ("false", False),
    ("False", False),
    ("FALSE", False),
]

bad_bools = [
    "tRUE",
    "truE",
    " True ",
    "  False   ",
    "fALSE",
    "FalsE",
]

good_ints = [
    ("5", 5),
    ("  7  ", 7),
    ("1.", 1),
]

bad_ints = [
    "2.45",
]

good_floats = [
    ("42.832", 42.832),
    (" 55.873 ", 55.873),
]

bad_floats = [
    "2.45.3",
    "1/0",
]


def _test_record(self, payload, instance):
    self.assertEqual(payload.get("sample_id", ""), instance.sample_id)
    self.assertEqual(payload.get("run_name", ""), instance.run_name)
    self.assertEqual(
        payload.get("collection_month"),
        instance.collection_month.strftime("%Y-%m")
        if instance.collection_month
        else None,
    )
    self.assertEqual(
        payload.get("received_month"),
        instance.received_month.strftime("%Y-%m") if instance.received_month else None,
    )
    self.assertEqual(
        payload.get("submission_date"),
        instance.submission_date.strftime("%Y-%m-%d")
        if instance.submission_date
        else None,
    )
    self.assertEqual(payload.get("country", ""), instance.country)
    self.assertEqual(payload.get("region", ""), instance.region)
    self.assertEqual(payload.get("concern"), instance.concern)
    self.assertEqual(payload.get("tests"), instance.tests)
    self.assertEqual(payload.get("score"), instance.score)

    if payload.get("records"):
        self.assertEqual(len(payload["records"]), instance.records.count())

        for subrecord in payload["records"]:
            subinstance = instance.records.get(test_id=subrecord.get("test_id"))
            self.assertEqual(subrecord.get("test_id"), subinstance.test_id)
            self.assertEqual(subrecord.get("test_pass"), subinstance.test_pass)
            self.assertEqual(
                subrecord.get("test_start"),
                subinstance.test_start.strftime("%Y-%m")
                if subinstance.test_start
                else None,
            )
            self.assertEqual(
                subrecord.get("test_end"),
                subinstance.test_end.strftime("%Y-%m")
                if subinstance.test_end
                else None,
            )
            self.assertEqual(subrecord.get("score_a"), subinstance.score_a)
            self.assertEqual(subrecord.get("score_b"), subinstance.score_b)
            self.assertEqual(subrecord.get("score_c"), subinstance.score_c)


class TestCreateView(OnyxTestCase):
    def setUp(self):
        super().setUp()
        self.endpoint = reverse("data.create", kwargs={"code": "test"})
        self.user = self.setup_user(
            "testuser",
            roles=["is_staff"],
            groups=[
                "add.project.test",
                "view.project.test",
            ],
        )

    def test_basic_ok(self):
        payload = copy.deepcopy(default_payload)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance)

    def test_nullables_ok(self):
        payload = copy.deepcopy(default_payload)
        payload.pop("collection_month")
        payload.pop("region")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance)

    def test_unpermissioned_viewable_field_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["cid"] = "helloooo"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_unpermissioned_unviewable_field_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["suppressed"] = "helloooo"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_unknown_fields_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["hello"] = "hi"
        payload["goodbye"] = "bye"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_required_fields_fail(self):
        payload = copy.deepcopy(default_payload)
        payload.pop("sample_id")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_required_fields_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["records"][0].pop("test_id")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_conditional_required_fields_fail(self):
        payload = copy.deepcopy(default_payload)
        payload.pop("country")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_conditional_required_fields_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["records"][0]["score_c"] = 42.3
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

        # Now we have all requirements for score_c
        payload = copy.deepcopy(default_payload)
        payload["records"][0]["score_a"] = 42.3
        payload["records"][0]["score_b"] = 42.3112
        payload["records"][0]["score_c"] = 42.4242
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance)

    def test_unique_together(self):
        payload = copy.deepcopy(default_payload)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 1
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance)

        payload = copy.deepcopy(default_payload)
        payload["sample_id"] = "sample-2345"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 2
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance)

        payload = copy.deepcopy(default_payload)
        payload["run_name"] = "run-2"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert TestModel.objects.count() == 3
        instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
        _test_record(self, payload, instance)

        payload = copy.deepcopy(default_payload)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 3
        assert (
            TestModel.objects.filter(sample_id=default_payload["sample_id"]).count()
            == 2
        )
        assert (
            TestModel.objects.filter(run_name=default_payload["run_name"]).count() == 2
        )

    def test_nested_unique_together(self):
        # NOTE: Just testing at the database level cause I am lazy
        payload = copy.deepcopy(default_payload)
        payload["records"][0]["test_id"] = payload["records"][1]["test_id"]
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_optional_value_group_fail(self):
        payload = copy.deepcopy(default_payload)
        payload.pop("collection_month")
        payload.pop("received_month")
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_optional_value_group_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["records"][0].pop("score_a", None)
        payload["records"][0].pop("score_b", None)
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_ordering_fail(self):
        # Testing ordering with yearmonths
        payload = copy.deepcopy(default_payload)
        payload["collection_month"] = "2023-02"
        payload["received_month"] = "2023-01"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

        # Testing ordering with integers
        payload = copy.deepcopy(default_payload)
        start = payload.pop("start")
        end = payload.pop("end")
        payload["end"] = start
        payload["start"] = end
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_nested_ordering_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["records"][1]["test_start"] = "2023-04"
        payload["records"][1]["test_end"] = "2023-03"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_charfield_too_long_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["sample_id"] = "A" * 1000 + "H"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_bad_yearmonth_fail(self):
        for bad_yearmonth in bad_yearmonths:
            payload = copy.deepcopy(default_payload)
            payload["collection_month"] = bad_yearmonth
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_future_yearmonth_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["collection_month"] = (datetime.today() + timedelta(days=60)).strftime(
            "%Y-%m"
        )
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_bad_date_fail(self):
        for bad_date in bad_dates:
            payload = copy.deepcopy(default_payload)
            payload["submission_date"] = bad_date
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_future_date_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["submission_date"] = (datetime.today() + timedelta(days=60)).strftime(
            "%Y-%m-%d"
        )
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_good_choice_ok(self):
        for good_choice, expected in good_choices:
            payload = copy.deepcopy(default_payload)
            payload["region"] = good_choice
            response = self.client.post(self.endpoint, data=payload)
            payload["region"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance)
            TestModel.objects.all().delete()

    def test_bad_choice_fail(self):
        for bad_choice in bad_choices:
            payload = copy.deepcopy(default_payload)
            payload["region"] = bad_choice
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_choice_constraint_fail(self):
        payload = copy.deepcopy(default_payload)
        payload["country"] = "wales"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

        payload = copy.deepcopy(default_payload)
        payload["region"] = "other"
        response = self.client.post(self.endpoint, data=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        assert TestModel.objects.count() == 0
        assert TestModelRecord.objects.count() == 0

    def test_good_bool_ok(self):
        for good_bool, expected in good_bools:
            payload = copy.deepcopy(default_payload)
            payload["concern"] = good_bool
            response = self.client.post(self.endpoint, data=payload)
            payload["concern"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance)
            TestModel.objects.all().delete()

    def test_bad_bool_fail(self):
        for bad_bool in bad_bools:
            payload = copy.deepcopy(default_payload)
            payload["concern"] = bad_bool
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_good_int_ok(self):
        for good_int, expected in good_ints:
            payload = copy.deepcopy(default_payload)
            payload["tests"] = good_int
            response = self.client.post(self.endpoint, data=payload)
            payload["tests"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance)
            TestModel.objects.all().delete()

    def test_bad_int_fail(self):
        for bad_int in bad_ints:
            payload = copy.deepcopy(default_payload)
            payload["tests"] = bad_int
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_good_float_ok(self):
        for good_float, expected in good_floats:
            payload = copy.deepcopy(default_payload)
            payload["score"] = good_float
            response = self.client.post(self.endpoint, data=payload)
            payload["score"] = expected
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            assert TestModel.objects.count() == 1
            instance = TestModel.objects.get(cid=response.json()["data"]["cid"])
            _test_record(self, payload, instance)
            TestModel.objects.all().delete()

    def test_bad_float_fail(self):
        for bad_float in bad_floats:
            payload = copy.deepcopy(default_payload)
            payload["score"] = bad_float
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_empty_request_fail(self):
        for payload in [None, {}]:
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0

    def test_bad_request_fail(self):
        for payload in [
            "",
            "hi",
            0,
            [],
            {"records": ""},
            {"records": "hi"},
            {"records": 0},
            {"records": {}},
            # {"sample_id": []},  # TODO: Should these all be lumped together?
            # {None: {}},
        ]:
            response = self.client.post(self.endpoint, data=payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            assert TestModel.objects.count() == 0
            assert TestModelRecord.objects.count() == 0
