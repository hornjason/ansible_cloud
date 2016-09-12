#!/bin/bash
for c in 0 1 2 3 ; do
  for b in `seq 0 9` ; do
    echo ----
    echo 172.31.${c}.21${b} 
    /usr/bin/ipmitool -I lanplus -H 172.31.${c}.21${b} -U root -P changeme chassis power status
  done
done
