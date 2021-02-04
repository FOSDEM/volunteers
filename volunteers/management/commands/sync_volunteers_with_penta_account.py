from django.core.management.base import BaseCommand
from volunteers.models import Edition, Task
from django.db import connections
import datetime
import logging


class Command(BaseCommand):

    def handle(self, *args, **options):
        for task in Task.objects.get(edition=Edition.get_current()):
            if task.talk_id is None and task.template.name.lower() not in ['Infodesk'.lower()]:
                continue
            for volunteer in task.volunteers:
                if not volunteer.penta_account_name:
                    continue
                if task.template.name.lower() in ['Infodesk'.lower()]:
                    # Harcoded because this works and will save me time
                    if task.date.weekday() == datetime.datetime.strptime('2021-02-06', '%Y-%m-%d').weekday():
                        # Saturday
                        event_id = '11762'
                    else:
                        # Sunday
                        event_id = '11763'
                else:
                    event_id = task.talk.ext_id
                logger = logging.getLogger("pentabarf")
                logger.debug("Values in insert: %s, %s" % (event_id, volunteer.penta_account_name))
                try:
                    with connections['pentabarf'].cursor() as cursor:
                        cursor.execute("""
                        insert into event_person (event_id, person_id, event_role,remark)
                        VALUES (%s,(select person_id from auth.account where login_name = %s),'host','volunteer')
                        on conflict on constraint event_person_event_id_person_id_event_role_key do nothing;
                        """, (event_id, volunteer.penta_account_name))
                except Exception as err:
                    logger.exception(err)
