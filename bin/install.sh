#!/bin/bash

MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

virtualenv ${MYDIR}/../virtualenv

source ${MYDIR}/../virtualenv/bin/activate

#pip install --upgrade pip
curl https://bootstrap.pypa.io/get-pip.py | python

pip install -r ${MYDIR}/../requirements.txt

bash
#deactivate
