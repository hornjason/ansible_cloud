#!/bin/python

import subprocess, time

cmd="/usr/bin/ipmitool -I lanplus -H 172.31.0.210 -U root -P changeme chassis power status"
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
power_status = p.stdout.read()

while "is on" in power_status:
    #print "Power is on:", power_status
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    power_status = p.stdout.read()
    if "is on" not in power_status:
        #print "Power is now off:", power_status
        break
    import os
    time.sleep(2)

