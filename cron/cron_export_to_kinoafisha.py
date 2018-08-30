#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.surkino import surkino_schedules_export_to_kinoafisha
from release_parser.rambler import rambler_schedules_export_to_kinoafisha
from release_parser.megamag import megamag_schedules_export_to_kinoafisha
from release_parser.kinohod import kinohod_schedules_export_to_kinoafisha
from release_parser.luxor import luxor_schedules_export_to_kinoafisha
from release_parser.luxor_chuvashia import luxor_chuvashia_schedules_export_to_kinoafisha
from release_parser.kinobit_cmc import kinobit_schedules_export_to_kinoafisha
from release_parser.planeta_kino import planeta_schedules_export_to_kinoafisha
from release_parser.nowru import nowru_player_to_kinoafisha
from release_parser.etaj import etaj_schedules_export_to_kinoafisha
from release_parser.cinemaarthall import cinemaarthall_schedules_export_to_kinoafisha
from release_parser.kinobklass import kinobklass_schedules_export_to_kinoafisha
from release_parser.zlat74ru import zlat74ru_schedules_export_to_kinoafisha
from release_parser.kinosaturn import kinosaturn_schedules_export_to_kinoafisha
from release_parser.zapad24ru import zapad24ru_schedules_export_to_kinoafisha
from release_parser.michurinskfilm import michurinskfilm_schedules_export_to_kinoafisha
from release_parser.kinoteatrua import kinoteatrua_schedules_export_to_kinoafisha
from release_parser.ktmir_and_ktrussia import ktmir_and_ktrussia_schedules_export_to_kinoafisha
from release_parser.arsenalclub import arsenalclub_schedules_export_to_kinoafisha
from release_parser.illuzion import illuzion_schedules_export_to_kinoafisha
from release_parser.vkinocomua import vkinocomua_schedules_export_to_kinoafisha
from release_parser.cinema5 import cinema5_schedules_export_to_kinoafisha
from release_parser.kinomonitor import kinomonitor_schedules_export_to_kinoafisha
from release_parser.oreanda_and_spartak import oreanda_and_spartak_schedules_export_to_kinoafisha
from release_parser.premierzal import premierzal_schedules_export_to_kinoafisha
from release_parser.kinomagnat import kinomagnat_schedules_export_to_kinoafisha

# ~20 min
##open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('luxor_schedules') + '\n')
luxor_schedules_export_to_kinoafisha()
##open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('luxor_chuvashia_schedules') + '\n')
luxor_chuvashia_schedules_export_to_kinoafisha()
##open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('illuzion_schedules') + '\n')
illuzion_schedules_export_to_kinoafisha()
##open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('kinobit_schedules') + '\n')
kinobit_schedules_export_to_kinoafisha() # ~112
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('megamag_schedules_') + '\n')
megamag_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('surkino_schedules') + '\n')
surkino_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('planeta_schedules') + '\n')
planeta_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('kinoteatrua_schedules') + '\n')
kinoteatrua_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('vkinocomua_schedules') + '\n')
vkinocomua_schedules_export_to_kinoafisha() # ~12
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('etaj_schedules') + '\n')
etaj_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('cinemaarthall_schedules') + '\n')
cinemaarthall_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('kinobklass_schedules') + '\n')
kinobklass_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('zlat74ru_schedules') + '\n')
zlat74ru_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('kinosaturn_schedules') + '\n')
kinosaturn_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('zapad24ru_schedules') + '\n')
zapad24ru_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('michurinskfilm_schedules') + '\n')
michurinskfilm_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('ktmir_and_ktrussia_schedules') + '\n')
ktmir_and_ktrussia_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('arsenalclub_schedules') + '\n')
arsenalclub_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('cinema5_schedules') + '\n')
cinema5_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('kinomonitor_schedules') + '\n')
kinomonitor_schedules_export_to_kinoafisha()
#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('nowru_player') + '\n')
oreanda_and_spartak_schedules_export_to_kinoafisha()

premierzal_schedules_export_to_kinoafisha()

kinomagnat_schedules_export_to_kinoafisha()

#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('kinohod_schedules') + '\n')
kinohod_schedules_export_to_kinoafisha() # ~176

#open('%s/export_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('rambler_schedules') + '\n')
rambler_schedules_export_to_kinoafisha() # ~197


nowru_player_to_kinoafisha()





