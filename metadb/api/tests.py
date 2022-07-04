from django.test import TestCase, Client
from data.models import Pathogen


class PathogenTestCase(TestCase):
    def setUp(self):
        Pathogen.objects.create(
            cid="sample1.run1",
            pathogen_code="pathogen",
            uploader="BIRM",
            sender_sample_id="sample1",
            run_name="run1",
            fasta_path="fastapath1",
            bam_path="bampath1",
            is_external=True,
            collection_date="2022-01-01",
            received_date="2022-01-02"
        )
        Pathogen.objects.create(
            cid="sample2.run1",
            pathogen_code="pathogen",
            uploader="BIRM",
            sender_sample_id="sample2",
            run_name="run1",
            fasta_path="fastapath2",
            bam_path="bampath2",
            is_external=True,
            collection_date="2022-01-01",
            received_date="2022-01-02"
        )
        self.client = Client()
    
    def test_get_pathogen(self):
        response = self.client.get('/api/get/pathogen/')
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_pathogen_by_cid(self):
        response_1 = self.client.get('/api/cid/get/sample1.run1/')
        response_2 = self.client.get('/api/cid/get/sample2.run1/')
        assert response_1.status_code == 200
        assert response_2.status_code == 200
