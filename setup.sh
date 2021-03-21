#!/bin/bash

python3 -m virtualenv venv
source venv/bin/activate

pip3 install -r requirements.txt

cd project
chmod u+x run.sh
./run.sh
