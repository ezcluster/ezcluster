

function wait_shutdown
{
	local SSH_OPTIONS="-t -t -q"
	STATE=$(ssh $SSH_OPTIONS $1 "sudo virsh dominfo ${2} | grep State"  2>/dev/null | awk '{ print $2$3 }')
	while [[ "$STATE" != *shutoff* ]]
	do
		printf " $3"
		sleep 2
		STATE=$(ssh $SSH_OPTIONS $1 "sudo virsh dominfo ${2} | grep State"  2>/dev/null | awk '{ print $2$3 }')
	done
	printf "\n"
}

function wait_ssh_up
{
	set +e
	nc -G 2 -z $1 22 >/dev/null
	ret=$?
	while [ $ret -ne 0 ] 
	do
		printf "."
		sleep 1
		nc -G 2 -z $1 22 >/dev/null
		ret=$?
	done
	printf "\n"
}


function ensure_ip_free
{
	echo "Will ensure $1 is not already in use.."
	ping -c 1 -t 2 $1 >/dev/null 2>&1
	if [ $? -eq 0 ]
	then
		echo "IP $1 IS ALIVE. Will not continue!!"
		exit 1
	fi
	echo "OK"
}

