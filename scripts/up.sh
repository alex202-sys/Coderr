    cd ~/projects/Coderr/
    git add .
    git commit -m "$*"
    git push
    ssh aleksandr_ogloblin_job@liuhequan.org "cd /home/aleksandr_ogloblin_job/projects/Coderr/ && sudo git pull" 
