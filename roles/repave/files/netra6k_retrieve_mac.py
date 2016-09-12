#!/bin/python
import pexpect, re, sys, os, time, shutil, subprocess

def _usage():
  print "incorrect syntax. Use:"
  print "\t" + sys.argv[0] + " <<nem ilom ip>> <<blade mgmt ip>> <<blade ilom ip>> <<blade id>>"
  print "\t" + "- nem ilom ip: IP Address"
  print "\t" + "- blade mgmt ip: IP Address"
  print "\t" + "- blade ilom ip: IP Address"
  print "\t" + "- blade id: cxxbyy"
  sys.exit(1)

def parse_find_mac(blade_number, sefos_output):
    mac = "_NoMac_Blade" + str(blade_number) + "_"
    for word in sefos_output.split():
        if re.match("00:1b", word):
            mac = word
    return mac

def change_mac_aging(tty, age):
    tty.sendline('configure terminal')
    tty.expect('.*SEFOS\(config\).*')
    tty.sendline('mac-address-table aging-time ' + str(age))
    tty.expect('.*SEFOS\(config\).*')
    tty.sendline('end')

def collect_mac_from_blade(tty, blade_number):
    blade_id = blade_number + 15
    tty.sendline('show mac-address-table interface ex 0/'+str(blade_id))
    tty.expect('.*Total.*')
    return parse_find_mac(blade_number, tty.after)

def establish_ssh_to_sefos(nem_ilom_ip):
    tty = pexpect.spawn('/usr/bin/ssh -o StrictHostKeyChecking=no root@'+nem_ilom_ip)
    import time
    time.sleep(1)
    tty.expect ('Password: ')
    p = tty.sendline('changeme')
    time.sleep(1)
    tty.expect('.*-> ')
    tty.sendline('cd /NEM/fs_cli/')
    tty.expect('.*SEFOS# ')
    return tty

def close_ssh(tty):
    tty.expect('.*SEFOS# ')
    tty.sendline('exit')

def pxeboot(blade_ilom_ip):
    cmd = "echo pxe booting: " + blade_ilom_ip + "  >> /tmp/.mac.out 2>&1"
    os.system(cmd)
    cmd = "/usr/bin/ipmitool -I lanplus -H " + blade_ilom_ip + " -U root -P changeme chassis power on >> /tmp/.mac.out 2>&1"
    os.system(cmd)
    time.sleep(5)
    cmd = "/usr/bin/ipmitool -I lanplus -H " + blade_ilom_ip + " -U root -P changeme chassis bootdev pxe >> /tmp/.mac.out 2>&1"
    os.system(cmd)
    cmd = "/usr/bin/ipmitool -I lanplus -H " + blade_ilom_ip + " -U root -P changeme chassis power cycle >> /tmp/.mac.out 2>&1"
    os.system(cmd)

def diskboot(blade_ilom_ip):
    cmd = "echo disk booting: " + blade_ilom_ip + "  >> /tmp/.mac.out 2>&1"
    os.system(cmd)
    cmd = "/usr/bin/ipmitool -I lanplus -H " + blade_ilom_ip + " -U root -P changeme chassis bootdev disk >> /tmp/.mac.out 2>&1"
    os.system(cmd)
    cmd = "/usr/bin/ipmitool -I lanplus -H " + blade_ilom_ip + " -U root -P changeme chassis power cycle >> /tmp/.mac.out 2>&1"
    os.system(cmd)

def poweroff(blade_ilom_ip):
    cmd = "echo powering off: " + blade_ilom_ip + "  >> /tmp/.mac.out 2>&1"
    os.system(cmd)
    cmd = "/usr/bin/ipmitool -I lanplus -H " + blade_ilom_ip + " -U root -P changeme chassis power off >> /tmp/.mac.out 2>&1"
    os.system(cmd)
    
    # now, we loop indefenitely until the blade power status is actually off
    cmd="/usr/bin/ipmitool -I lanplus -H " + blade_ilom_ip + " -U root -P changeme chassis power status"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    power_status = p.stdout.read()
    
    while "is on" in power_status:
        #print "Power is on:", power_status
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        power_status = p.stdout.read()
        if "is on" not in power_status:
            #print "Power is now off:", power_status
            break
        time.sleep(2)


def stop_dhcpd():
    cmd = "/sbin/service dhcpd stop >> /tmp/.mac.out 2>&1"
    os.system(cmd)

def start_dhcpd():
    cmd = "/sbin/service dhcpd start >> /tmp/.mac.out 2>&1"
    os.system(cmd)

def wait_for_mac(tty, blade_number, blade_ilom_ip):    
    stop_dhcpd()
    pxeboot(blade_ilom_ip)
    while True:
        time.sleep(10)
        #print "sleeping 10s and retrying to get the mac"
        mac = collect_mac_from_blade(tty, blade_number)
        if not re.match("_NoMac_Blade", mac):
            break
    # We now poer off the blades to avoid them coming online
    #diskboot(blade_ilom_ip)
    poweroff(blade_ilom_ip)
    #start_dhcpd()
    return mac

def add_header_to_file(machosts_file_name):
  if not os.path.exists(machosts_file_name):
    machosts_file = open(machosts_file_name, 'w')
    machosts_file.write("mac:\n")
    machosts_file.close()
  return machosts_file_name
    
def write_mac_to_file(machosts_file_name, blade_id, mac):
  # if the mac file does not exist, we add the tag "mac:" at the begining of it
  ##add_header_to_file(machosts_file_name)
  machosts_file = open(machosts_file_name, 'a+')
  
  tmp_file_name = "/tmp/.mac_hosts_temp_file_" + blade_id
  tmp_file = open(tmp_file_name, 'w')
  
  for line in machosts_file:
    if blade_id not in line:
      tmp_file.write(line)
  
  tmp_file.write("  " + blade_id + ": " + mac + "\n")
  tmp_file.close()
  machosts_file.close()
  
  shutil.copy2(tmp_file_name, machosts_file_name)

def wake_up_blade(blade_mgmt_ip): 
  # recompose the mgmt ip address of the blade from blade_ilom_ip
  #ip_address = blade_ilom_ip.split('.')
  #net_id = ip_address[0] + "." + ip_address[1]
  #chassis_short_id = ip_address[2]
  #blade_short_id = str((int(ip_address[3])-100))
  #mgmt_ip = net_id + "." + chassis_short_id + "." + blade_short_id
  cmd = "echo trying to ssh the blade: " + blade_mgmt_ip + "  >> /tmp/.mac.out 2>&1"
  os.system(cmd)
  cmd = "ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null " + blade_mgmt_ip + " true >> /tmp/.mac.out 2>&1"
  os.system(cmd)
    
# Main
if len(sys.argv) is not 5:
  _usage()

nem_ilom_ip = sys.argv[1]
blade_mgmt_ip = sys.argv[2]
blade_ilom_ip = sys.argv[3]
blade_id = sys.argv[4]

# Retrieve the blade number / slot
blade_number = blade_id[len(blade_id)-1:]

machosts_file_name = "/tmp/mac/mac_" + blade_id

# establish connection to NEM0
tty = establish_ssh_to_sefos(nem_ilom_ip)

# change mac-address-table aging-time to 1 hour (3600s)
change_mac_aging(tty, 3600)

# perform preliminary ping to "wake up" the blade and have the nem get his mac address
wake_up_blade(blade_mgmt_ip)

# collect the mac address of the wanted blade
mac = collect_mac_from_blade(tty, int(blade_number))

# if the mac address was not retrieved, we pxeboot the blade to force it to broadcast the mac address
if re.match("_NoMac_Blade", mac):
    mac = wait_for_mac(tty, int(blade_number), blade_ilom_ip)

# then we populate the mac file
write_mac_to_file(machosts_file_name, blade_id, mac)

# restore mac-address-table aging-time to 5 minutes (300s)
change_mac_aging(tty, 600)

# close ssh connection
close_ssh(tty)

#tty.interact()
tty.close()

sys.exit(0)

