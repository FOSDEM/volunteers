from django.core.management.base import BaseCommand #, CommandError
from volunteers.models import Edition


class Command(BaseCommand):

    def handle(self, *args, **options):
        Edition.sync_with_penta()
