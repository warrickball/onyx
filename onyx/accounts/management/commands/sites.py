import json
from pydantic import BaseModel
from typing import Optional, List
from django.core.management import base
from .site import create_site


class SiteConfig(BaseModel):
    code: str
    description: Optional[str]
    projects: Optional[List[str]]


class SitesConfig(BaseModel):
    sites: List[SiteConfig]


class Command(base.BaseCommand):
    help = "Create sites."

    def add_arguments(self, parser):
        parser.add_argument("sites_config")
        parser.add_argument("--quiet", action="store_true")

    def print(self, *args, **kwargs):
        if not self.quiet:
            print(*args, **kwargs)

    def handle(self, *args, **options):
        self.quiet = options["quiet"]

        with open(options["sites_config"]) as sites_config_file:
            sites_config = SitesConfig.model_validate(json.load(sites_config_file))

        self.create_sites(sites_config)

    def create_sites(self, sites_config: SitesConfig):
        """
        Create/update a set of sites.
        """

        for site_config in sites_config.sites:
            create_site(
                self,
                site_config.code,
                description=site_config.description,
                projects=site_config.projects,
            )
