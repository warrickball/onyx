from rest_framework.test import APITestCase
from .models import Pathogen


class CreatePathogenTestCase(APITestCase):
    def setUp(self):
        Pathogen.objects.create(
            cid="C-01234",
            pathogen_code="pathogen",
            institute="BIRM",
            sender_sample_id="sample1",
            run_name="run1",
            fasta_path="fastapath",
            bam_path="bampath",
            is_external=True,
            collection_date="2022-01-01",
            received_date="2022-01-02"
        )
        self.endpoint = "/api/create/"
    
    def test_create(self):
        response = self.client.post(
            self.endpoint,
            {
                "cid" : "C-56789",
                "pathogen_code" : "pathogen",
                "institute" : "BIRM",
                "sender_sample_id" : "sample2",
                "run_name" : "run1",
                "fasta_path" : "fastapath",
                "bam_path" : "bampath",
                "is_external" : False,
                "collection_date" : "2022-04-03",
                "received_date" : "2022-01-09"
            },
            format="json"
        )
        assert response.status_code == 200
        assert Pathogen.objects.filter(cid="C-56789").count() == 1

        response = self.client.post(
            self.endpoint,
            {
                "cid" : "C-01234",
                "pathogen_code" : "pathogen",
                "institute" : "BIRM",
                "sender_sample_id" : "sample1",
                "run_name" : "run1",
                "fasta_path" : "fastapath",
                "bam_path" : "bampath",
                "is_external" : True,
                "collection_date" : "2022-01-01",
                "received_date" : "2022-01-02"
            },
            format="json"
        )
        assert response.status_code == 400
        assert Pathogen.objects.filter(cid="C-01234").count() == 1


class GetPathogenTestCase(APITestCase):
    def setUp(self):
        Pathogen.objects.create(
            cid="C-01234",
            pathogen_code="pathogen",
            institute="BIRM",
            sender_sample_id="sample1",
            run_name="run1",
            fasta_path="fastapath",
            bam_path="bampath",
            is_external=True,
            collection_date="2022-01-01",
            received_date="2022-01-02"
        )
        Pathogen.objects.create(
            cid="C-56789",
            pathogen_code="pathogen",
            institute="BIRM",
            sender_sample_id="sample2",
            run_name="run1",
            fasta_path="fastapath",
            bam_path="bampath",
            is_external=False,
            collection_date="2022-04-03",
            received_date="2022-01-09"
        )
        self.pathogen_endpoint = "/api/get"
        self.cid_endpoint = "/api/cid/get"
    
    def test_get(self):
        response = self.client.get(f"{self.pathogen_endpoint}/pathogen/")
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = self.client.get(f"{self.pathogen_endpoint}/not-a-pathogen/")
        assert response.status_code == 404

        response = self.client.get(f"{self.pathogen_endpoint}/pathogen/?cid=C-01234")
        assert response.status_code == 200
        assert len(response.json()) == 1

        response = self.client.get(f"{self.pathogen_endpoint}/pathogen/?institute=BIRM")
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = self.client.get(f"{self.pathogen_endpoint}/pathogen/?institute=BIRM&sender_sample_id=sample2")
        assert response.status_code == 200
        assert len(response.json()) == 1

        response = self.client.get(f"{self.pathogen_endpoint}/pathogen/?collection_date__lte=2022-04-04")
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = self.client.get(f"{self.pathogen_endpoint}/pathogen/?collection_date__lte=2022-04-02")
        assert response.status_code == 200
        assert len(response.json()) == 1

        response = self.client.get(f"{self.pathogen_endpoint}/pathogen/?collection_date__lte=2021-12-31")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_by_cid(self):
        response = self.client.get(f"{self.cid_endpoint}/C-01234/")
        assert response.status_code == 200

        response = self.client.get(f"{self.cid_endpoint}/C-56789/")
        assert response.status_code == 200

        response = self.client.get(f"{self.cid_endpoint}/C-00000/")
        assert response.status_code == 404


class UpdatePathogenTestCase(APITestCase):
    def setUp(self):
        Pathogen.objects.create(
            cid="C-01234",
            pathogen_code="pathogen",
            institute="BIRM",
            sender_sample_id="sample1",
            run_name="run1",
            fasta_path="fastapath",
            bam_path="bampath",
            is_external=True,
            collection_date="2022-01-01",
            received_date="2022-01-02"
        )
        self.pathogen_endpoint = "/api/update"
        self.cid_endpoint = "/api/cid/update"

    def test_update(self):
        response = self.client.put(
            f"{self.pathogen_endpoint}/not-a-pathogen/C-01234/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 404

        response = self.client.patch(
            f"{self.pathogen_endpoint}/not-a-pathogen/C-01234/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 404

        response = self.client.put(
            f"{self.pathogen_endpoint}/pathogen/C-56789/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 404

        response = self.client.patch(
            f"{self.pathogen_endpoint}/pathogen/C-56789/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 404

        response = self.client.put(
            f"{self.pathogen_endpoint}/pathogen/C-01234/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 400

        response = self.client.patch(
            f"{self.pathogen_endpoint}/pathogen/C-01234/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 200
        assert Pathogen.objects.get(cid="C-01234").is_external == False

    def test_update_by_cid(self):
        response = self.client.put(
            f"{self.cid_endpoint}/C-56789/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 404

        response = self.client.patch(
            f"{self.cid_endpoint}/C-56789/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 404

        response = self.client.put(
            f"{self.cid_endpoint}/C-01234/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 400

        response = self.client.patch(
            f"{self.cid_endpoint}/C-01234/",
            {
                "is_external" : False
            }
        )
        assert response.status_code == 200
        assert Pathogen.objects.get(cid="C-01234").is_external == False


class DeletePathogenTestCase(APITestCase):
    def setUp(self):
        Pathogen.objects.create(
            cid="C-01234",
            pathogen_code="pathogen",
            institute="BIRM",
            sender_sample_id="sample1",
            run_name="run1",
            fasta_path="fastapath",
            bam_path="bampath",
            is_external=True,
            collection_date="2022-01-01",
            received_date="2022-01-02"
        )
        self.pathogen_endpoint = "/api/delete"
        self.cid_endpoint = "/api/cid/delete"

    def test_delete(self):
        response = self.client.delete(f"{self.cid_endpoint}/C-56789/")
        assert response.status_code == 404

    def test_delete_by_cid(self):
        pass
