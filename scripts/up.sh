#!/bin/bash
cd ~/projects/Coderr/ || exit
git add .
git commit -m "$*"
git push

# ssh -o ForwardAgent=yes aleksandr_ogloblin_job@liuhequan.org "cd /home/aleksandr_ogloblin_job/projects/Coderr/ && git pull"

# No SSH connection required to start directly on VS! Run the pull directly locally::
cd /home/aleksandr_ogloblin_job/projects/Coderr/ && git pull
 
