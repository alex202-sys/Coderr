#!/bin/bash
cd ~/Coderr/ || exit
git add .
git commit -m "$*"
git push
git pull
 
