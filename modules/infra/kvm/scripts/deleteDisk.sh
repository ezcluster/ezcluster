#!/bin/bash

set -e


SSH_OPTIONS="-t -t -q"


function usage {
	echo 'deleteDisk --host <host> --name <VM_name>  --volume <Volume(vol0-4)> --device <vd[a-x])'
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
		--volume)
			VOLUME=$2
			shift
		;;
		--device)
			DEVICE=$2
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
if [ "$VOLUME" = "" ]; then echo "Missing --volume parameters";	exit 1; fi
if [ "$DEVICE" = "" ]; then echo "Missing --device parameters";	exit 1; fi

DISK_IMG=${VOLUME}/libvirt/images/${NAME}_${DEVICE}.qcow2

ssh $SSH_OPTIONS $HOST "sudo rm ${DISK_IMG}"




