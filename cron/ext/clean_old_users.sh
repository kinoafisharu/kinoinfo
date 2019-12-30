#!/bin/bash
#
#
DIR="/public/kinoinfo/cron"
source /public/env/bin/activate
DX=`date`
SX=`basename "$0"`
echo $DX __ $SX >> $DIR/ext/cron.log 2>&1
/public/env/bin/python  $DIR/clean_old_users.py >> $DIR/ext/cron.log 2>&1
