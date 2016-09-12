#!/bin/python
import sys, yaml

# Usage:
# python ./loop.py <<cloud name>> <<nb chassis>> <<nb utility servers>> <<nb zfs>> <<nb es2 switches>>
def _usage():
  print "incorrect syntax. Use:"
  print "\t" + sys.argv[0] + " <<cloud name>> <<nb chassis>> <<nb utility servers>> <<nb zfs>> <<nb es2 switches>>"
  print "\t" + "- cloud name: 4 chars + 2 digits, shall be unique in the lab"
  print "\t" + "- nb chassis: digit always <= 100"
  print "\t" + "- nb utility servers: digit always <= 15"
  print "\t" + "- nb zfs: digit always <= 50"
  print "\t" + "- nb es2 switches: digit always <= 10"
  sys.exit(1)

def _print_infrastructure(infra_id, infra_file):
  infra_file.write("infrastructure:\n")
  infra_file.write(x2sp + "infra_id: " + infra_id + "\n")

def _print_vlans(infra_file, lab_specifics_data):
  infra_file.write(x2sp + "vlans:" + "\n")
    
  infra_file.write(x4sp + "openstack_vxlan_tenant:" + "\n")
  infra_file.write(x6sp + "id: 16" + "\n")
  infra_file.write(x6sp + "network: 172.16.0.0" + "\n")
  infra_file.write(x6sp + "netmask: 255.255.0.0" + "\n")
  infra_file.write(x6sp + "defined:" + "\n")
  infra_file.write(x8sp + "- nem0" + "\n")
  infra_file.write(x8sp + "- es2_72_tenant" + "\n")
  
  infra_file.write(x4sp + "storage:" + "\n")
  infra_file.write(x6sp + "id: 30" + "\n")
  infra_file.write(x6sp + "network: 172.30.0.0" + "\n")
  infra_file.write(x6sp + "netmask: 255.255.0.0" + "\n")
  infra_file.write(x6sp + "defined:" + "\n")
  infra_file.write(x8sp + "- nem1" + "\n")
  infra_file.write(x8sp + "- es2_72_storage" + "\n")
  
  vlan_name = ["int_management_vlan", "ext_management_vlan", "ilom_vlan", "openstack_provider_vlan"]
  net_element = ["vlan_id", "tagged_traffic_needed", "network", "netmask", "broadcast", "host_min", "host_max", "gateway", "ntp_server", "name_server", "name_server_search", "defined"]
  for v in vlan_name:
    infra_file.write(x4sp + v + ":" + "\n")
    for n in net_element:
      try:
        val = str(lab_specifics_data["lab_specifics"]["vlans"][v][n])
        infra_file.write(x6sp + n + ": " + val + "\n")
      except:
        ##pass
        if v == "int_management_vlan":
          infra_file.write(x6sp + "vlan_id: 1" + "\n")
          infra_file.write(x6sp + "tagged_traffic_needed: false" + "\n")
          infra_file.write(x6sp + "network: 172.31.0.0" + "\n")
          infra_file.write(x6sp + "netmask: 255.255.0.0" + "\n")
          infra_file.write(x6sp + "defined: ['nem0']" + "\n")
          break
        if v != "int_management_vlan" and n == "tagged_traffic_needed":
           infra_file.write(x6sp + "tagged_traffic_needed: false" + "\n")
        else:
          pass

  infra_file.write("\n")

def _print_switches(infra_file, number_of_es2, hosts_file):
  infra_file.write(x2sp + "switches:" + "\n")
  hosts_file.write("# es2-72 switches:\n")
  for es2 in range(0, number_of_es2):
    es2_72_tenant_id = "es2_72_tenant_" + "%02d" % (es2,)
    es2_72_storage_id = "es2_72_storage_" + "%02d" % (es2,)
    
    es2_72_tenant_last_digit_ip = es2 + 120
    es2_72_storage_last_digit_ip = es2 + 130
    
    es2_72_tenant_ilom_ip = "172.31.0." + str(es2_72_tenant_last_digit_ip)
    es2_72_storage_ilom_ip = "172.31.0." + str(es2_72_storage_last_digit_ip)
    
    infra_file.write(x4sp + es2_72_tenant_id + ":" + "\n")
    infra_file.write(x6sp + "es2_72_ilom_ip: " + es2_72_tenant_ilom_ip + "\n")
    hosts_file.write(es2_72_tenant_ilom_ip + "\t" + es2_72_tenant_id + "\n")

    infra_file.write(x4sp + es2_72_storage_id + ":" + "\n")
    infra_file.write(x6sp + "es2_72_ilom_ip: " + es2_72_storage_ilom_ip + "\n")
    hosts_file.write(es2_72_storage_ilom_ip + "\t" + es2_72_storage_id + "\n")
    
  infra_file.write("\n")
  
def _print_zfs(number_of_zfs, infra_file, hosts_file):
  infra_file.write(x2sp + "zfs:" + "\n")
  hosts_file.write("# zfs:\n")
  for zfs in range(0, number_of_zfs):
    zfs_id = "zfs" + "%02d" % (zfs,)
    infra_file.write(x4sp + zfs_id + ":" + "\n")
    
    # Ilom
    try:
      zfs_ilom_head00_ip = lab_specifics_data["lab_specifics"]["vlans"]["ilom_vlan"]["zfs"][zfs_id]["head00"]
      zfs_ilom_head01_ip = lab_specifics_data["lab_specifics"]["vlans"]["ilom_vlan"]["zfs"][zfs_id]["head01"]
    except:      
      zfs_ilom_head00_ip = "172.31." + str(zfs) + ".247"
      zfs_ilom_head01_ip = "172.31." + str(zfs) + ".248"

    infra_file.write(x6sp + "zfs_ilom_head00_ip: " + zfs_ilom_head00_ip + "\n")
    infra_file.write(x6sp + "zfs_ilom_head01_ip: " + zfs_ilom_head01_ip + "\n")
    hosts_file.write(zfs_ilom_head00_ip + "\t" + zfs_id + "head00_sp" + "\n")
    hosts_file.write(zfs_ilom_head01_ip + "\t" + zfs_id + "head01_sp" + "\n")
    
    # Management
    try:
      zfs_mgmt_head00_ip = lab_specifics_data["lab_specifics"]["vlans"]["ext_management_vlan"]["zfs"][zfs_id]["head00"]
      zfs_mgmt_head01_ip = lab_specifics_data["lab_specifics"]["vlans"]["ext_management_vlan"]["zfs"][zfs_id]["head01"]
    except:      
      zfs_mgmt_head00_ip = "172.31." + str(zfs) + ".249"
      zfs_mgmt_head01_ip = "172.31." + str(zfs) + ".250"

    infra_file.write(x6sp + "zfs_mgmt_head00_ip: " + zfs_mgmt_head00_ip + "\n")
    infra_file.write(x6sp + "zfs_mgmt_head01_ip: " + zfs_mgmt_head01_ip + "\n")
    hosts_file.write(zfs_mgmt_head00_ip + "\t" + zfs_id + "head00_mg" + "\n")
    hosts_file.write(zfs_mgmt_head01_ip + "\t" + zfs_id + "head01_mg" + "\n")

    # Storage
    zfs_storage_head00_ip = "172.30." + str(zfs) + ".247"
    zfs_storage_head01_ip = "172.30." + str(zfs) + ".248"
    zfs_storage_virtual_ip = "172.30." + str(zfs) + ".249"    
    
    infra_file.write(x6sp + "zfs_storage_head00_ip: " + zfs_storage_head00_ip + "\n")
    infra_file.write(x6sp + "zfs_storage_head01_ip: " + zfs_storage_head01_ip + "\n")
    infra_file.write(x6sp + "zfs_storage_virtual_ip: " + zfs_storage_virtual_ip + "\n")
    hosts_file.write(zfs_storage_head00_ip + "\t" + zfs_id + "head00_st" + "\n")
    hosts_file.write(zfs_storage_head01_ip + "\t" + zfs_id + "head01_st" + "\n")
    hosts_file.write(zfs_storage_virtual_ip + "\t" + zfs_id + "vip_st" + "\n")

  infra_file.write("\n")
  
def _print_dhcp_subnets(infra_id, infra_file, lab_specifics_data):
  infra_file.write(x2sp + "dhcp_subnets:" + "\n")
  infra_file.write(x4sp + "info:" + "\n")
  
  try:
    base = lab_specifics_data["lab_specifics"]["vlans"]["int_management_vlan"]["network"]
    infra_file.write(x6sp + "base: "  + base + "\n")
  except:
    infra_file.write(x6sp + "base: 172.31.0.0" + "\n")
  
  try:
    netmask = lab_specifics_data["lab_specifics"]["vlans"]["int_management_vlan"]["netmask"]
    infra_file.write(x6sp + "netmask: "  + netmask + "\n")
  except:
    infra_file.write(x6sp + "netmask: 255.255.0.0" + "\n")
  
  try:
    router = lab_specifics_data["lab_specifics"]["vlans"]["int_management_vlan"]["gateway"]
    infra_file.write(x6sp + "routers: "  + router + "\n")
  except:
    infra_file.write(x6sp + "routers: 172.31.254.254" + "\n")
    
  userv_id = infra_id + "%02d" % (0,)
  try:
    nextserver_ip = lab_specifics_data["lab_specifics"]["vlans"]["int_management_vlan"]["utility_servers"][userv_id]
    infra_file.write(x6sp + "next_server: "  + nextserver_ip + "\n")
  except:
    infra_file.write(x6sp + "next_server: 172.31.254.254" + "\n")
  
  infra_file.write("\n")

def _print_utility_servers(infra_id, number_of_userv, infra_file, hosts_file, lab_specifics_data):
  infra_file.write(x2sp + "utility_servers:" + "\n")
  hosts_file.write("# utility servers:\n")
  for userv in range(0, number_of_userv):
    userv_id = infra_id + "%02d" % (userv,)
    infra_file.write(x4sp + userv_id + ":" + "\n")
    infra_file.write(x6sp + "userv_id: " + userv_id + "\n")
    
    userv_last_digit_ip = userv + 240
    userv_ilom_ip = "172.31.50." + str(userv_last_digit_ip)
    infra_file.write(x6sp + "userv_ilom_ip:  " + userv_ilom_ip + "\n")
    hosts_file.write(userv_ilom_ip + "\t" + userv_id + "_sp" + "\n")
  
    #userv_int_mgmt_ip = "172.31.51." + str(userv_last_digit_ip)
    #infra_file.write(x6sp + "userv_int_mgmt_ip: " + userv_int_mgmt_ip + "\n")
    #hosts_file.write(userv_int_mgmt_ip + "\t" + userv_id + "\n")
    try:
      userv_int_mgmt_ip = lab_specifics_data["lab_specifics"]["vlans"]["int_management_vlan"]["utility_servers"][userv_id]
      infra_file.write(x6sp + "userv_int_mgmt_ip: " + userv_int_mgmt_ip + "\n")
      userv_int_mgmt_vlan_id = str(lab_specifics_data["lab_specifics"]["vlans"]["int_management_vlan"]["vlan_id"])
      infra_file.write(x6sp + "userv_int_mgmt_vlan_id: " + userv_int_mgmt_vlan_id + "\n")
    except:
      userv_int_mgmt_ip = "172.31.51." + str(userv_last_digit_ip)
      infra_file.write(x6sp + "userv_int_mgmt_ip: " + userv_int_mgmt_ip + "\n")
      hosts_file.write(userv_int_mgmt_ip + "\t" + userv_id + "\n")
      pass
    
    try:
      userv_ext_mgmt_ip = lab_specifics_data["lab_specifics"]["vlans"]["ext_management_vlan"]["utility_servers"][userv_id]
      infra_file.write(x6sp + "userv_ext_mgmt_ip: " + userv_ext_mgmt_ip + "\n")
      userv_ext_mgmt_vlan_id = str(lab_specifics_data["lab_specifics"]["vlans"]["ext_management_vlan"]["vlan_id"])
      infra_file.write(x6sp + "userv_ext_mgmt_vlan_id: " + userv_ext_mgmt_vlan_id + "\n")
    except:
      pass
    
  infra_file.write("\n")
  
def _print_chassis_blades(infra_id, number_of_chassis, infra_file, hosts_file, lab_specifics_data):
  infra_file.write(x2sp + "chassis:" + "\n")
  hosts_file.write("# chassis 'c..', nems 'c..n..' and blades 'c..b..':\n")
  for chassis in range(0, number_of_chassis):
      cmm_id = "c" + "%02d" % (chassis,)
      infra_file.write(x4sp + cmm_id + ":" + "\n")
      infra_file.write(x6sp + "cmm_id: " + cmm_id + "\n")

      try:
        cmm_ilom_ip = lab_specifics_data["lab_specifics"]["vlans"]["ilom_vlan"]["cmms"][cmm_id]
      except:      
        cmm_ilom_ip = "172.31." + str(chassis) + ".253"
        
      infra_file.write(x6sp + "cmm_ilom_ip: " + cmm_ilom_ip + "\n")

      cmm_long_id = infra_id + cmm_id
      hosts_file.write(cmm_ilom_ip + "\t" + cmm_id + "\n")
      
      # NEMs
      infra_file.write(x6sp + "nems:" + "\n")
      for nem in range(0, 2):
        nem_id = cmm_id + "n" + "%02d" % (nem,)
        infra_file.write(x8sp + nem_id + ":" + "\n")
        infra_file.write(x10sp + "nem_id: " + nem_id + "\n")
        
        # if nem ilom ip is defined in the lab_specifics_file then we use it otherwise we compute this value
        try:
          nem_ilom_ip = lab_specifics_data["lab_specifics"]["vlans"]["ilom_vlan"]["nems"][nem_id]
        except:
          nem_last_digit_ip = nem + 251
          nem_ilom_ip = "172.31." + str(chassis) + "." + str(nem_last_digit_ip)
         
        infra_file.write(x10sp + "nem_ilom_ip: " + nem_ilom_ip + "\n")
        
        nem_long_id = infra_id + nem_id
        hosts_file.write(nem_ilom_ip + "\t" + nem_id + "\n")
      
      # BLADEs
      infra_file.write(x6sp + "blades:" + "\n")
      for blade in range(0, 10):
        blade_id = cmm_id + "b" + "%02d" % (blade,)
        infra_file.write(x8sp + blade_id + ":" + "\n")
        infra_file.write(x10sp + "blade_id: " + blade_id + "\n")
        infra_file.write(x10sp + "blade_hostname: " + blade_id + "\n")
        
        # if ilom ip is defined in the lab_specifics_file then we use it otherwise we compute this value
        try:
          blade_ilom_ip = lab_specifics_data["lab_specifics"]["vlans"]["ilom_vlan"]["blades"][blade_id]
          blade_ilom_vlan_id = str(lab_specifics_data["lab_specifics"]["vlans"]["ilom_vlan"]["vlan_id"])
          infra_file.write(x10sp + "blade_ilom_ip: " + blade_ilom_ip + "\n")
          infra_file.write(x10sp + "blade_ilom_vlan_id: " + blade_ilom_vlan_id + "\n")
        except:
          blade_last_digit_ilom_ip = blade + 210
          blade_ilom_ip = "172.31." + str(chassis) + "." + str(blade_last_digit_ilom_ip)
          infra_file.write(x10sp + "blade_ilom_ip: " + blade_ilom_ip + "\n")
          
        hosts_file.write(blade_ilom_ip + "\t" + blade_id + "_sp" + "\n")
          
        # ################
        # if internal ip is defined in the lab_specifics_file then we use it otherwise we compute this value
        try:
          blade_int_mgmt_ip = lab_specifics_data["lab_specifics"]["vlans"]["int_management_vlan"]["blades"][blade_id]
          infra_file.write(x10sp + "blade_int_mgmt_ip: " + blade_int_mgmt_ip + "\n")
        except:
          blade_last_digit_nonilom_ip = blade + 110
          blade_int_mgmt_ip = "172.31." + str(chassis) + "." + str(blade_last_digit_nonilom_ip)
          infra_file.write(x10sp + "blade_int_mgmt_ip: " + blade_int_mgmt_ip + "\n")
          
        hosts_file.write(blade_int_mgmt_ip + "\t" + blade_id +"\n")

        #blade_last_digit_nonilom_ip = blade + 110
        #blade_int_mgmt_ip = "172.31." + str(chassis) + "." + str(blade_last_digit_nonilom_ip)
        #        
        #infra_file.write(x10sp + "blade_int_mgmt_ip: " + blade_int_mgmt_ip + "\n")
        #hosts_file.write(blade_int_mgmt_ip + "\t" + blade_id + "\n")
        # ################
        
        # if an external management IP is defined in the lab_specifics_file then we add it
        try:
          blade_ext_mgmt_ip = lab_specifics_data["lab_specifics"]["vlans"]["ext_management_vlan"]["blades"][blade_id]
          infra_file.write(x10sp + "blade_ext_mgmt_ip: " + blade_ext_mgmt_ip + "\n")
          hosts_file.write(blade_ext_mgmt_ip + "\t" + blade_id + "_ext" + "\n")
          blade_ext_mgmt_vlan_id = str(lab_specifics_data["lab_specifics"]["vlans"]["ext_management_vlan"]["vlan_id"])
          infra_file.write(x10sp + "blade_ext_mgmt_vlan_id: " + blade_ext_mgmt_vlan_id + "\n")
        except:
          pass
        
        blade_last_digit_nonilom_ip = blade + 110
        blade_vlan16_ip = "172.16." + str(chassis) + "." + str(blade_last_digit_nonilom_ip)
        infra_file.write(x10sp + "blade_vlan16_ip: " + blade_vlan16_ip + "\n")
        hosts_file.write(blade_vlan16_ip + "\t" + blade_id + "_tn" + "\n")
          
        blade_vlan30_ip = "172.30." + str(chassis) + "." + str(blade_last_digit_nonilom_ip)
        infra_file.write(x10sp + "blade_vlan30_ip: " + blade_vlan30_ip + "\n")
        hosts_file.write(blade_vlan30_ip + "\t" + blade_id + "_st" + "\n")
            
      infra_file.write("\n")
  
#./loop.py <<cloud name>> <<nb chassis>> <<nb utility servers>> <<nb zfs>> <<nb es2 switches>>
if len(sys.argv) is not 6:
  _usage()
  
infra_id = sys.argv[1]
number_of_chassis = int(sys.argv[2])
number_of_userv = int(sys.argv[3])
number_of_zfs = int(sys.argv[4])
number_of_es2 = int(sys.argv[5])

if number_of_chassis > 100 or number_of_userv > 15 or number_of_zfs > 48 or number_of_es2 > 10:
  _usage()

# Global constants
x2sp =  "  "
x4sp =  "    "
x6sp =  "      "
x8sp =  "        "
x10sp = "          "

lab_specifics_file_name = "/root/onap21/group_vars/lab_specifics.yml"
infra_file_name = "/root/onap21/roles/generate_vars/vars/main.yml"
hosts_file_name = "/root/onap21/repo/hosts"
infra_file = open(infra_file_name, 'w')
hosts_file = open(hosts_file_name, 'w')

# Main
# Load lab_specifics.yml in a variable for access later
with open(lab_specifics_file_name, 'r') as lab_specifics_file:
  lab_specifics_data = yaml.load(lab_specifics_file)
  
_print_infrastructure(infra_id, infra_file)
_print_vlans(infra_file, lab_specifics_data)
_print_switches(infra_file, number_of_es2, hosts_file)
_print_zfs(number_of_zfs, infra_file, hosts_file)
_print_dhcp_subnets(infra_id, infra_file, lab_specifics_data)
_print_utility_servers(infra_id, number_of_userv, infra_file, hosts_file, lab_specifics_data)
_print_chassis_blades(infra_id, number_of_chassis, infra_file, hosts_file, lab_specifics_data)

hosts_file.close()
sys.exit()
