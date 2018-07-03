#!/bin/bash

set -e

SSH_OPTIONS="-t -t -q"

function usage {
	echo 'attachDisk --host <host> --name <VM_name> --size <Disk_size_in_GB> --volume <Volume(vol0-4)> --device <vd[a-x]>  --dmode <thin|thick>'
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
		--size)
			SIZE=$2
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
		--dmode)
			DMODE=$2
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
if [ "$SIZE" = "" ]; then echo "Missing --size parameters";	exit 1; fi
if [ "$VOLUME" = "" ]; then echo "Missing --volume parameters";	exit 1; fi
if [ "$DEVICE" = "" ]; then echo "Missing --device parameters";	exit 1; fi
if [ "$DMODE" = "" ]; then echo "Missing --dmode parameters"; usage; exit 1; fi
if [ "$DMODE" != "thin" -a "$DMODE" != "thick" ]; then echo "--dmode value must be 'thin' or 'thick'"; usage; exit 1; fi 

DISK_IMG=${VOLUME}/libvirt/images/${NAME}_${DEVICE}.qcow2

set +e
ssh $SSH_OPTIONS $HOST "ls $DISK_IMG" >/dev/null
if [ $? -eq 0 ]; then echo "DISK ${DISK_IMG} ALREADY EXISTING ON ${HOST}!!!. WILL STOP"; exit 1; fi 
set -e

ssh $SSH_OPTIONS $HOST "sudo qemu-img create -f qcow2 -o preallocation=metadata ${DISK_IMG} ${SIZE}G"

if [ "$DMODE" == "thick" ]
then
	ssh $SSH_OPTIONS $HOST "sudo fallocate -l ${SIZE}G ${DISK_IMG}"
fi

ssh $SSH_OPTIONS $HOST "sudo virsh attach-disk --domain ${NAME} --source ${DISK_IMG} --target ${DEVICE} --persistent --driver qemu --subdriver qcow2 --type disk --sourcetype file"



