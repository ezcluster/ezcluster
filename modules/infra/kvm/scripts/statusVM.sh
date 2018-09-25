#!/bin/bash

set +e


SSH_OPTIONS="-t"

function usage {
    echo 'statusVM --host <host> --name <VM_name>'
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
        *)
            echo "Unknown parameter $1"
            usage
            exit 1
        ;;
    esac
    shift
done

if [ "$NAME" = "" ]; then echo "Missing --name parameters"; usage; exit 1; fi
if [ "$HOST" = "" ]; then echo "Missing --host parameters"; usage; exit 1; fi


STATE=$(ssh $SSH_OPTIONS $HOST "sudo virsh dominfo ${NAME} | grep State"  2>/dev/null | awk '{ print $2$3 }')

echo "$HOST: $NAME $STATE"


