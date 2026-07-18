#!/bin/bash
cd ~/projects/Coderr/ || exit
git add .
git commit -m "$*"
git push
ssh -a aleksandr_ogloblin_job@liuhequan.org "cd /home/aleksandr_ogloblin_job/projects/Coderr/ && git pull" 
