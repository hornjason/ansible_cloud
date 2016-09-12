#!/bin/python
import yaml

with open('group_vars/lab_specifics.yml', 'r') as f:
  doc = yaml.load(f)
  

txt = doc["lab_specifics"]["lab_id"]
print txt


txt = doc["lab_specifics"]["vlans"]["management_vlan"]["blades"]["c00b04"]
print txt
