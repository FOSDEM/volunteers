from django.core.management.base import BaseCommand
from volunteers.models import Edition


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        if len(args) <= 0:
            raise Exception(
                'Please specify a file name (xml) with the task list (use the same format as init_data).'
            )
        Edition.create_from_task_list(args[0])
