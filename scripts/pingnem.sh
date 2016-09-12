#!/bin/bash

for chassis in 0 1 2 3 ; do
    ping -c 1 172.31.${chassis}.251 > /dev/null 2>&1 && echo ping 172.31.${chassis}.251 success || echo ping 172.31.${chassis}.251 failure!!!
    ping -c 1 172.31.${chassis}.252 > /dev/null 2>&1 && echo ping 172.31.${chassis}.252 success || echo ping 172.31.${chassis}.252 failure!!!
done

