
#version=RHEL7
# System authorization information
auth --enableshadow --passalgo=sha512
# Use graphical install
text
# Run the Setup Agent on first boot
firstboot --disable
eula --agreed
reboot
# Use CDROM installation media
cdrom
ignoredisk --only-use={{ boot_dev }}
# Keyboard layouts
keyboard --vckeymap=us --xlayouts='us'
# System language
lang en_US.UTF-8

# Disable NetworkManager
services --disabled=NetworkManager --enabled=network

network --bootproto=dhcp --device={{ management_interface }} --onboot=yes --noipv6
repo --name="Server-HighAvailability" --baseurl=file:///run/install/repo/addons/HighAvailability
repo --name="Server-ResilientStorage" --baseurl=file:///run/install/repo/addons/ResilientStorage
# Root password
rootpw --iscrypted $6$4gTOWpB0LDnsmA7B$yWehnDMNXyA2EIp5i1zm3nbac.SJl4hOuEb3CDKXeIFKfC3zWP7N0iP1ybF/STh0DBAuEfbinTrTV23ppmExh1
#SELINUX
selinux --disable
# System timezone
timezone America/New_York --isUtc
# System bootloader configuration
bootloader --append=" crashkernel=auto" --location=mbr --boot-drive={{ boot_dev }}

# Partition clearing information
zerombr
clearpart --all --drives={{ boot_dev }}
# Disk partitioning information
part /boot --fstype "ext4" --ondisk={{ boot_dev }} --size=476 --asprimary
part swap  --fstype swap --ondisk={{ boot_dev }} --size=4096
part pv.01  --size=10000 --grow --ondisk={{ boot_dev }}

##part btrfs.274 --fstype="btrfs" --ondisk="{{ boot_dev }}" --size=500000
##btrfs none --label=ol --data=single btrfs.274
##btrfs /var --subvol   --name=var_lib_docker LABEL=ol

#volgroup
volgroup ol --pesize=4096 pv.01
logvol /     --fstype "xfs" --name=root --vgname=ol --size=500000 --grow
#logvol /home --fstype xfs --name=home --vgname=ol --size=20000
#logvol /var  --fstype xfs --name=var  --vgname=ol --size=50000
logvol swap  --fstype swap --name=swap --vgname=ol --size=4096



%packages
@base
@compat-libraries
@core
@debugging
@development
@network-file-system-client
@security-tools
@virtualization-hypervisor
@virtualization-platform
@virtualization-client
@virtualization-tools
kexec-tools
ntp
gcc
libguestfs-tools
xauth
screen
net-tools
tcpdump
-NetworkManager
-firewalld
-libvirt-daemon

%end


%post

echo "PERSISTENT_DHCLIENT=1 " >> /etc/sysconfig/network-scripts/ifcfg-{{ management_interface }}

%end

