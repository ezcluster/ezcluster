#!/bin/bash


MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[  -f /etc/redhat-release ]]
then
	echo "On a RHEL or Centos system."
	echo "Assuming python3,virtualenv and python3-pip already installed"
	echo "else: sudo yum install python3 python3-pip python-virtualenv "
	VENV=venv_rhel
	virtualenv -p python3  "${MYDIR}/../${VENV}"
  # shellcheck disable=SC1090
  source "${MYDIR}"/../${VENV}/bin/activate
  pip install --upgrade pip
  pip install -r "${MYDIR}"/requirements.txt
elif [[ "$OSTYPE" == "darwin"* ]]
then
	echo "On a MacOS system."
	VENV=venv
	echo "Assuming python3 virtualenv and python3 pip already installed"
	PYTHON=$(type python3 | awk '{ print $3 }')
	if [  ! -x "$PYTHON" ]
	then
		echo "Missing python3 interpreter"
		exit 1
	fi
	virtualenv --python="$PYTHON" "${MYDIR}"/../${VENV}
  # shellcheck disable=SC1090
  source "${MYDIR}"/../${VENV}/bin/activate
  pip install --upgrade pip
  pip install -r "${MYDIR}"/requirements.txt
else
	echo
	echo "Not on a RHEL or Centos or MacOs system. Exiting!"
	# shellcheck disable=SC2034
	read a
	exit 1
fi

