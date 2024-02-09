#!/bin/bash
date=$(date '+%Y-%m-%d')
newname=$"bk_tuftregistry_${date}.txt"
linecount=$(wc -l /home/user/fastai/tuftregistry.txt)
echo "linecount of registry:"$linecount
mv /home/user/fastai/tuftregistry.txt /home/user/fastai/$newname
touch /home/user/fastai/tuftregistry.txt

