#!/bin/bash
#
# N.B. this need sudoers edit (visudo)
#
source /var/www/kinoinfo/data/www/env2018/bin/activate
cd /var/www/kinoinfo/data/www/kinoinfo
sudo -u apache /var/www/kinoinfo/data/www/env2018/bin/python /var/www/kinoinfo/data/www/kinoinfo/ext2017/imdb_btn_upd.py