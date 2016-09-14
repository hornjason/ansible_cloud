#!/usr/bin/env bash

####################
# disalbe sslVerificitaion for git
# git config --global http.proxy http://rmdc-proxy.oracle.com:80
# edit ~/.gitconfig and add below to allow cloning of git repo from https
# sslVerify = false
####################
# enable proxy for this server
####################
ENABLE_PROXY="true"

####################
# vnc port
####################
VNC_PORT="99"

####################
# packages to install
####################
package_list="vim virt-install libvirt libguestfs-tools libguestfs git asciidoc rpm-build python2-devel \
python-pip python-devel sshpass python-httplib2 python-paramiko python-keyczar tigervnc-server pexpect  \
git gcc libffi-devel openssl-devel"

####################
# packages to remove
####################
package_remove_list="firewalld NetworkManager gnome-packagekit"

####################
yum_conf="/etc/yum.conf"
####################


####################
# proxy server
####################
proxy=" proxy=http://www-proxy.us.oracle.com:80"

####################
# whoami
####################
whobei=`whoami`
if [[ $whobei == "root" ]];then SUDO="";else SUDO=`which sudo`;fi

################################
# setup oracle proxy for yum
################################
if [[ $ENABLE_PROXY =~ ^[tT] ]]; then
  if [[ $(grep -c proxy $yum_conf) == 0 ]]; then
      echo "Adding proxy $proxy to $yum_conf"
      $SUDO sed -ie "\$a$proxy" $yum_conf
  fi
  export http_proxy="http://www-proxy.us.oracle.com:80"
  export https_proxy="http://www-proxy.us.oracle.com:80"
  printf -v no_proxy '%s,' 172.31.2.{1..255};
  export no_proxy="localhost,127.0.0.1,us.oracle.com,$no_proxy,10.75.138.39"

#git_proxy="git config --global http.proxy http://www-proxy.us.oracle.com:80"
#git_proxys="git config --global https.proxy http://www-proxy.us.oracle.com:443"
fi
#

################################
# setup vnc server
################################
echo "VNC: Setting up VNC on port $VNC_PORT"
$SUDO yum -y install tigervnc-server
passwd="changeme"
# set vncpasswd

$SUDO cp /lib/systemd/system/vncserver@.service /etc/systemd/system/vncserver@.service
$SUDO sed -i "s/<USER>/$whobei/g" /etc/systemd/system/vncserver@.service
$SUDO sed -i 's/vncserver %i"/vncserver %i -geometry 1280x1024"/' /etc/systemd/system/vncserver@.service

$SUDO mkdir ~/.vnc
$SUDO chmod 600 ~/.vnc
$SUDO echo $passwd | vncpasswd -f > ~/.vnc/passwd
$SUDO chmod -R 600 ~/.vnc

echo "VNC: enabling/starting service"
$SUDO systemctl daemon-reload
$SUDO systemctl enable vncserver@:$VNC_PORT.service
$SUDO systemctl start vncserver@:$VNC_PORT.service
echo "VNC: Done"

################################
# setup .bash_profile 
################################
cat > /.bash_profile << EOF
# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
        . ~/.bashrc
fi

# User specific environment and startup programs

PATH=$PATH:$HOME/bin

export PATH

EOF

################################
# setup .bashrc
################################
#if [[ ! -e ~/.bashrc ]]; then
echo "BASHRC: backing up current .bashrc"
cp ~/.bashrc ~/bashrc.bak

echo "BASHRC: creating new one"

cat > ~/.bashrc << EOF
force_color_prompt=yes

    export PS1="[\u@\[\e[00;31m\]\h\[\e[0m\]:\[\e[00;36m\]UTILITY\[\e[0m\]:\t: \w]# "
unset color_prompt force_color_prompt
EOF

if [[ $ENABLE_PROXY =~ ^[tT] ]]; then
cat >> ~/.bashrc << EOF
export http_proxy=http://www-proxy.us.oracle.com:80
export https_proxy=http://www-proxy.us.oracle.com:80
EOF
fi

echo "BASHRC: Done"
echo "BASHRC: Sourcing .bashrc"
. ~/.bash_profile


################################
# setup .vimrc
################################
echo "VIMRC: Checking vimrc"
if [[ ! -e ~/.vimrc ||  $(grep -c tabstop ~/.vimrc 2>/dev/null) == 0 ]]; then
    echo "set tabstop=4 softtabstop=0 expandtab shiftwidth=4 smarttab" >> ~/.vimrc
    echo "set bg=dark" >> ~/.vimrc
elif [[ $(grep -c tabstop ~/.vimrc 2>/dev/null) == 0 ]]; then
    echo "set tabstop=4 softtabstop=0 expandtab shiftwidth=4 smarttab" >> ~/.vimrc
fi
echo "VIMRC: Done"
################################
# install packages/repos
################################
echo "Updating ALL packges"
#$SUDO yum --disablerepo=* --enablerepo=ol7_latest,ol7_UEKR3 update

if [[ $(yum repolist | grep -ic epel ) == 0 ]]; then
  echo "Installing EPEL YUM Repol"
  $SUDO yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
fi

echo "waiting for yum to clean up"
sleep 60

echo "Removing packages not needed"
  $SUDO systemctl disable firewalld
  $SUDO iptables -F
  $SUDO yum --enablerepo=epel,ol7_optional_latest -y remove $package_remove_list

echo "Installing package list"
  $SUDO yum --enablerepo=epel,ol7_optional_latest -y install $package_list

################################
# setup git globals
################################


################################
# install ansible 2.0 from git
################################
pip install ansible==2.1.1

#if [[ $(rpm -qa |grep -c ansible) == 0 ]]; then
#    cd /usr/src
#    #for stable checkout stable branch
#    $SUDO git clone https://github.com/ansible/ansible.git --recursive -b stable-2.1
#    cd ansible
#    $SUDO make rpm
#    $SUDO yum -y install rpm-build/*noarch.rpm
#fi
################################
# pip install 
################################
echo "PIP: Installing shade"
pip install shade
################################
# update pxe ansible_host= 
################################
#pxe_ip=$(/sbin/ifconfig|awk '/172.31.51/ {print $2}') 
#sed -i "s/172.31.254.254/$pxe_ip/g" hosts
#sed -i "s/pxe_boot_server:.*/pxe_boot_server: $pxe_ip/" group_vars/all

