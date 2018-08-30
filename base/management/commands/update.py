# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.tracker import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        if 1:
            start_afisha_importer = (2,8,18,22)
            t = time.localtime()
            logger(3, u'Start cron|event:x10|', 'a')
            logger(3, u'Start cron(topick_loader)|event:x11|', 'a')
            topick_loader(0)
            logger(3, u'Finish cron(topick_loader)|event:x31|', 'a')
            logger(3, u'Start cron(topick_cleaner)|event:x12|', 'a')
            topick_cleaner(0)
            logger(3, u'Finish cron(topick_cleaner)|event:x22|', 'a')
            if t.tm_hour in start_afisha_importer:
                logger(3, u'Start cron(afisha_importer)|event:x14|', 'a')
                afisha_importer(0)
                logger(3, u'Finish cron(afisha_importer)|event:x34|', 'a')
