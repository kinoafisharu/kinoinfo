#!/bin/bash
#
#
DIR="/var/www/kinoinfo/data/www/kinoinfo/cron"
source /var/www/kinoinfo/data/www/env2018/bin/activate
cd /var/www/kinoinfo/data/www/kinoinfo
DX=`date`
SX=`basename "$0"`
echo $DX __ $SX >> $DIR/ext/cron.log 2>&1
#echo `date` >> $DIR/ext/cron.log 2>&1
/var/www/kinoinfo/data/www/env2018/bin/python  $DIR/cron_cinemate_cc.py >> $DIR/ext/cron.log 2>&1