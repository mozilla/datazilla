import os

from django.core.management.base import BaseCommand
from django.core.cache import cache

from datazilla.model import DataSource

class Command(BaseCommand):

    help = (
            "Reset the datasource cache"
            )

    def handle(self, *args, **options):

        DataSource.reset_cache()
