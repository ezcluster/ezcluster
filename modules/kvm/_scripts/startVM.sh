#!/bin/bash

set +e
set +x


SSH_OPTIONS="-t -t -q"

MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $MYDIR/functions.sh


function usage {
	echo 'startVM --host <host> --name <VM_name> --fqdn <VM_fqdn>'
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
		--fqdn)
			FQDN=$2
			shift
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
if [ "$FQDN" = "" ]; then echo "Missing --fqdn parameters";	usage; exit 1; fi

echo "Starting the VM ${NAME}"

ssh $SSH_OPTIONS $HOST "sudo virsh start ${NAME}" 
		 
echo "Waiting for the VM ${NAME} to be ssh ready"
wait_ssh_up $FQDN
echo "$NAME Up and running"



