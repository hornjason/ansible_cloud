#!/bin/bash

for c in $(seq 0 3) ; do
    echo "chassis $c"
    for b in $(seq 0 9) ; do
        blade=172.31.${c}.21${b}
        echo -en "$blade:"
        s=$(ipmitool -I lanplus -H ${blade} -Uroot -Pchangeme chassis power status)
        echo $s | grep -i off
        if [ $? != 1 ]; then s=$s" !!!!!!!!!!!" ; fi
        echo -en " $s \n"
    done
    echo  -en "\n" 
done
