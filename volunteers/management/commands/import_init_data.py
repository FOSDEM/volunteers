from django.core.management.base import BaseCommand
from volunteers.models import Edition


class Command(BaseCommand):

    def handle(self, *args, **options):
        Edition.init_generic_tasks()
