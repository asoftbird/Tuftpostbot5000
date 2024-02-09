#!/usr/bin/bash
#tpblauncher.sh
# execute python script

cd / 
cd /home/user/fastai
source venv/bin/activate
python util/bskysession.py
python -W ignore tuftpostbotrewrite.py
deactivate
cd /

