from django.core.management.base import BaseCommand
from volunteers.models import Task, TaskTemplate


class Command(BaseCommand):

    def handle(self, *args, **options):
        if len(args) <= 0:
            valid_choices = ', '.join([tt.name for tt in TaskTemplate.objects.all()])
            raise Exception(
                "Please specify the type of task you would like to delete as the first argument, e.g. ./manage.py delete_tasks Heralding.\n"
                "Specify 'all' to delete all tasks.\n"
                "The types of task in the system are {}".format(valid_choices)
            )
        if args[0].lower() == 'all':
            Task.objects.all().delete()
        else:
            Task.objects.filter(template__name=args[0]).delete()
