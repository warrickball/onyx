from rest_framework.test import APITestCase
from rest_framework import status
from .models import Pathogen, generate_cid
from accounts.models import Institute, User
import secrets
import random
import json
import os


# TODO: Tests for choice fields


def create_institutes():
    codes = []
    institute_a = Institute.objects.create(code="UNIA", name="University of A") # NOTE: institute codes now have to be capital or everything dies
    codes.append(institute_a.code)
    institute_b = Institute.objects.create(code="DEPTB", name="Department of B")
    codes.append(institute_b.code)
    return codes


def generate_pathogen_dict(institute_code):
    sender_sample_id = f"SAMPLE-{secrets.token_hex(3).upper()}"
    run_name = f"RUN-{random.randint(1, 100)}"
    pathogen_dict = {
        "institute" : institute_code,
        "sender_sample_id" : sender_sample_id,
        "run_name" : run_name,
        "pathogen_code" : "PATHOGEN",
        "fasta_path" : f"{sender_sample_id}.{run_name}.fasta",
        "bam_path" : f"{sender_sample_id}.{run_name}.bam",
        "is_external" : random.choice([True, False]),
        "collection_month" : f"{random.choice(['2021', '2022'])}-{random.randint(1, 12)}",
        "received_month" : f"{random.choice(['2021', '2022'])}-{random.randint(1, 12)}"
    }
    return pathogen_dict


def populate_pathogen_table(amount, institute_code):
    pathogen_instances = []
    for _ in range(amount):
        pathogen_dict = generate_pathogen_dict(institute_code)
        pathogen_dict["institute"] = Institute.objects.get(code=institute_code)
        pathogen_dict["pathogen_code"] = "PATHOGEN"
        instance = Pathogen.objects.create(**pathogen_dict)
        pathogen_instances.append(instance)
    return pathogen_instances # NOTE: (obviously) future updates to records in db aren't reflected in instances


def create_input_pathogen_data(amount, institute_code):
    input_pathogen_data = []
    for _ in range(amount):
        pathogen_dict = generate_pathogen_dict(institute_code)
        input_pathogen_data.append(pathogen_dict)
    return input_pathogen_data


class BaseAPITestCase(APITestCase):
    def setup_approved_authed_user(self, username, institute):
        response = self.client.post(
            "/accounts/register/",
            data={
                "username" : username,
                "password" : "pass123456",
                "email" : "user@user.com",
                "institute" : institute
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=username)
        user.is_approved = True
        self.client.force_authenticate(user) # type: ignore
        return user


class CreatePathogenTestCase(BaseAPITestCase):
    def setUp(self):
        self.endpoint = "/data/pathogen/"
        self.institute_codes = create_institutes()
        self.pathogen_db_instances = []
        for code in self.institute_codes:
            self.pathogen_db_instances.extend(populate_pathogen_table(50, institute_code=code))
        self.institute = self.institute_codes[0]
        self.wrong_institute = self.institute_codes[1]
        self.user = self.setup_approved_authed_user("user", self.institute)
        self.user_input_size = 100

    def test_valid(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        for x in input_data:
            response = self.client.post(
                self.endpoint,
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 1)
    
    def test_cant_provide_cid(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        for x in input_data:
            x["cid"] = generate_cid()
            response = self.client.post(
                self.endpoint,
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 0)
    
    def test_must_provide_institute(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        for x in input_data:
            x.pop("institute")
            response = self.client.post(
                self.endpoint,
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 0)
     
    def test_wrong_institute(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.wrong_institute)
        for x in input_data:
            response = self.client.post(
                self.endpoint,
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 0)
    
    def test_incorrect_endpoint(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        for x in input_data:
            response = self.client.post(
                "/data/not-a-pathogen/",
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 0)

    def test_mismatch_pathogen_code(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        for x in input_data:
            x["pathogen_code"] = "different-pathogen"
            response = self.client.post(
                self.endpoint,
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 0)

    def test_sample_and_run_preexisting(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        for x in input_data:
            instance = random.choice(self.pathogen_db_instances)
            x["sender_sample_id"] = instance.sender_sample_id
            x["run_name"] = instance.run_name
            response = self.client.post(
                self.endpoint,
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 1)

    def test_sample_or_run_preexisting(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        vals = set(range(0, len(self.pathogen_db_instances)))
        for x in input_data:
            chosen_val = random.choice(list(vals))
            vals.remove(chosen_val)
            instance = self.pathogen_db_instances[chosen_val]
            coin = random.randint(0, 1)
            if x["run_name"] == instance.run_name: # Prevent test failing if their run_name already matches, which is not unlikely
                pass
            elif coin:
                x["sender_sample_id"] = instance.sender_sample_id
            else:
                x["run_name"] = instance.run_name
            response = self.client.post(
                self.endpoint,
                data=x,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 1)
    
    def test_required_field_missing(self):
        input_data = create_input_pathogen_data(amount=self.user_input_size, institute_code=self.institute)
        fields = list(input_data[0].keys())
        for x in input_data:
            field_to_remove = random.choice(fields)
            x_missing_field = dict(x)
            x_missing_field.pop(field_to_remove)
            response = self.client.post(
                self.endpoint,
                data=x_missing_field,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Pathogen.objects.filter(sender_sample_id=x["sender_sample_id"]).filter(run_name=x["run_name"]).count(), 0)
    
    def test_optional_field_missing(self):
        pass # TODO make some optional fields and test them
    

class GetPathogenTestCase(BaseAPITestCase):
    def setUp(self):
        self.endpoint = "/data/pathogen/"
        self.institute_codes = create_institutes()
        self.pathogen_db_instances = []
        for code in self.institute_codes:
            self.pathogen_db_instances.extend(populate_pathogen_table(50, institute_code=code))
        self.institute = self.institute_codes[0]
        self.wrong_institute = self.institute_codes[1]
        self.user = self.setup_approved_authed_user("user", self.institute)

    def test_valid(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), Pathogen.objects.count())     

    def test_valid_filtered(self):
        response = self.client.get(
            self.endpoint,
            data={
                "collection_month__gte" : "2022-04"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), Pathogen.objects.filter(collection_month__gte="2022-04").count()) 
        response = self.client.get(
            self.endpoint,
            data={
                "collection_month__gte" : "2022-01",
                "received_month__lte" : "2022-08",
                "run_name__contains" : "5"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), Pathogen.objects.filter(collection_month__gte="2022-01").filter(received_month__lte="2022-08").filter(run_name__contains="5").count())    

    def test_valid_filtered_institute(self):
        for code in self.institute_codes:
            response = self.client.get(
                self.endpoint,
                data={
                    "institute__code" : code
                }
            ) 
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.json()["results"]), Pathogen.objects.filter(institute__code=code).count())
            response = self.client.get(
                self.endpoint,
                data={
                    "institute" : code # A hardcoded default for better or worse
                }
            ) 
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.json()["results"]), Pathogen.objects.filter(institute__code=code).count())

    def test_empty(self):
        response = self.client.get(
            self.endpoint,
            data={
                "collection_month__gt" : "2022-01",
                "collection_month__lt" : "2022-01",
                "run_name__contains" : "5"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), Pathogen.objects.filter(collection_month__gt="2022-01").filter(collection_month__lt="2022-01").filter(run_name__contains="5").count())  

    def test_invalid_pathogen_code(self):
        response = self.client.get(f"/data/not-a-pathogen/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_id_provided_for_filtering(self):
        for i in range(10):
            response = self.client.get(
                self.endpoint,
                data={
                    "id" : i
                }
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_id_provided_for_filtering_sneaky(self):
        for i in range(10):
            response = self.client.get(
                self.endpoint,
                data={
                    "id__lte" : i,
                    "id__gte" : i
                }
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for i in range(10):
            response = self.client.get(
                self.endpoint,
                data={
                    "institute_id__gte" : i
                }
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for i in range(10):
            response = self.client.get(
                self.endpoint,
                data={
                    "institute__id__lte" : i
                }
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtering_field_ending_with_id_but_its_not_database_id_so_its_ok(self):
        for i in range(10):
            response = self.client.get(
                self.endpoint,
                data={
                    "sender_sample_id" : i,
                    "sender_sample_id__gte" : i
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.json()["results"]), Pathogen.objects.filter(sender_sample_id=i).count())  

    def test_invalid_filter_params(self):
        response = self.client.get(
            self.endpoint,
            data={
                "is_external" : "HELLO THERE"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(
            self.endpoint,
            data={
                "institat" : "NOT A FIELD"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(
            self.endpoint,
            data={
                "cid__containss" : "C-123456"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_paginated_response(self):
        pass # TODO: Quite a hefty one to test


class UpdatePathogenTestCase(BaseAPITestCase):
    def setUp(self):
        self.endpoint = "/data/pathogen/"
        self.institute_codes = create_institutes()
        self.pathogen_db_instances = []
        for code in self.institute_codes:
            self.pathogen_db_instances.extend(populate_pathogen_table(50, institute_code=code))
        self.institute = self.institute_codes[0]
        self.wrong_institute = self.institute_codes[1]
        self.user = self.setup_approved_authed_user("user", self.institute)

    def test_valid_patch(self):
        for instance in self.pathogen_db_instances:
            if instance.institute == self.user.institute:
                cid = instance.cid
                if instance.is_external == True:
                    is_external_replacement = False
                else:
                    is_external_replacement = True
                data={
                    "is_external" : is_external_replacement
                }
                response = self.client.patch(
                    os.path.join(self.endpoint, cid + "/"),
                    data=data

                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)
                self.assertEqual(Pathogen.objects.get(cid=cid).is_external, is_external_replacement)

    def test_patch_wrong_institute(self):
        for instance in self.pathogen_db_instances:
            if instance.institute != self.user.institute:
                cid = instance.cid
                if instance.is_external == True:
                    previous_value = True
                    is_external_replacement = False
                else:
                    previous_value = False
                    is_external_replacement = True
                data={
                    "is_external" : is_external_replacement
                }
                response = self.client.patch(
                    os.path.join(self.endpoint, cid + "/"),
                    data=data

                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)
                self.assertEqual(Pathogen.objects.get(cid=cid).is_external, previous_value)

    def test_patch_readonly_fields(self):
        for instance in self.pathogen_db_instances:
            if instance.institute == self.user.institute:
                cid = instance.cid
                instance_before_update = {k : v for k, v in Pathogen.objects.get(cid=cid).__dict__.items() if k != "_state"}
                for field in list(Pathogen.readonly_fields()):
                    data={
                        field : "some-value"
                    }

                    response = self.client.patch(
                        os.path.join(self.endpoint, cid + "/"),
                        data=data
                    )
                    instance_after_update = {k : v for k, v in Pathogen.objects.get(cid=cid).__dict__.items() if k != "_state"}
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)
                    self.assertEqual(instance_before_update, instance_after_update)
                    self.assertEqual(json.loads(response.content), {"unknown" : [], "forbidden" : [field]}) # type: ignore

    def test_patch_unknown_fields(self):
        for instance in self.pathogen_db_instances:
            if instance.institute == self.user.institute:
                cid = instance.cid
                instance_before_update = {k : v for k, v in Pathogen.objects.get(cid=cid).__dict__.items() if k != "_state"}
                data={
                    "unknown-field" : "some-value"
                }

                response = self.client.patch(
                    os.path.join(self.endpoint, cid + "/"),
                    data=data
                )
                instance_after_update = {k : v for k, v in Pathogen.objects.get(cid=cid).__dict__.items() if k != "_state"}
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)
                self.assertEqual(instance_before_update, instance_after_update)
                self.assertEqual(json.loads(response.content), {"unknown" : ["unknown-field"], "forbidden" : []}) # type: ignore

    def test_patch_no_fields(self):
        for instance in self.pathogen_db_instances:
            if instance.institute == self.user.institute:
                cid = instance.cid
                instance_before_update = {k : v for k, v in Pathogen.objects.get(cid=cid).__dict__.items() if k != "_state"}
                response = self.client.patch(
                    os.path.join(self.endpoint, cid + "/"),
                    data={}
                )
                instance_after_update = {k : v for k, v in Pathogen.objects.get(cid=cid).__dict__.items() if k != "_state"}
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)
                self.assertEqual(instance_before_update, instance_after_update)

    def test_put(self):
        for instance in self.pathogen_db_instances:
            if instance.institute == self.user.institute:
                cid = instance.cid
                if instance.is_external == True:
                    previous_value = True
                    is_external_replacement = False
                else:
                    previous_value = False
                    is_external_replacement = True
                data={
                    "is_external" : is_external_replacement
                }
                response = self.client.put(
                    os.path.join(self.endpoint, cid + "/"),
                    data=data

                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)
                self.assertEqual(Pathogen.objects.get(cid=cid).is_external, previous_value)


class DeletePathogenTestCase(BaseAPITestCase):
    def setUp(self):
        self.endpoint = "/data/pathogen/"
        self.institute_codes = create_institutes()
        self.pathogen_db_instances = []
        for code in self.institute_codes:
            self.pathogen_db_instances.extend(populate_pathogen_table(50, institute_code=code))
        self.institute = self.institute_codes[0]
        self.wrong_institute = self.institute_codes[1]
        self.user = self.setup_approved_authed_user("user", self.institute)

    def test_valid_not_admin(self):
        for instance in self.pathogen_db_instances:
            cid = instance.cid
            response = self.client.delete(os.path.join(self.endpoint, cid + "/"))
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)

    def test_valid(self):
        self.user.is_staff = True
        self.user.save()
        for instance in self.pathogen_db_instances:
            cid = instance.cid
            response = self.client.delete(os.path.join(self.endpoint, cid + "/"))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 0)

    def test_cid_not_found(self):
        self.user.is_staff = True
        self.user.save()
        for _ in range(10):
            cid = generate_cid()
            response = self.client.delete(os.path.join(self.endpoint, cid + "/"))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_pathogen_code(self):
        self.user.is_staff = True
        self.user.save()
        for instance in self.pathogen_db_instances:
            cid = instance.cid
            response = self.client.delete(os.path.join(f"/data/delete/not-a-pathogen/", cid + "/"))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(Pathogen.objects.filter(cid=cid).count(), 1)
