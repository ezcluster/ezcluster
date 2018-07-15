#!/bin/bash

set +e


SSH_OPTIONS="-t -t -q"

MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $MYDIR/functions.sh

function usage {
	echo 'stopVM --host <host> --name <VM_name> [--force]'
}

while [[ $# > 0 ]]
do
	case $1 in
		--name)
			NAME=$2
			shift
		;;
		--host)
			HOST=$2
			shift
		;;
		--force)
			FORCE=Y
		;;		
		*)
			echo "Unknown parameter $1"
			usage
			exit 1
		;;
	esac
	shift
done

if [ "$NAME" = "" ]; then echo "Missing --name parameters"; usage; exit 1; fi
if [ "$HOST" = "" ]; then echo "Missing --host parameters";	usage; exit 1; fi

ssh $SSH_OPTIONS $HOST "sudo virsh list --all" | grep ${NAME}
if [ "$?" -ne "0" ]
then
	echo "${HOST}: ${NAME} not existing"
	exit 1
fi


if [[ "$FORCE" == Y ]]
then
	echo "Force stopping the VM ${NAME}"
	ssh $SSH_OPTIONS $HOST "sudo virsh destroy ${NAME}"
else
	echo "Stopping the VM ${NAME}"
	ssh $SSH_OPTIONS $HOST "sudo virsh shutdown ${NAME}"
fi
wait_shutdown $HOST $NAME "Waiting $NAME down\n"				 



