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
# master repo that contains rdo packages
####################
MASTER_REPO="10.240.121.66"

####################
# proxy server
####################
proxy="http://adc-proxy.oracle.com:80"

####################
# OpenStack Release
####################
OPENSTACK_RELEASE=mitaka
#OPENSTACK_RELEASE=newton

####################
# END OF CONFIG
####################

####################
# packages to install
####################
package_list="vim virt-install libvirt libguestfs-tools libguestfs git asciidoc rpm-build python2-devel \
python-pip python-devel sshpass python-httplib2 python-paramiko python-keyczar tigervnc-server pexpect  \
gcc libffi-devel openssl-devel createrepo"

####################
# packages to remove
####################
package_remove_list="firewalld NetworkManager gnome-packagekit"

####################
yum_conf="/etc/yum.conf"
####################

####################
# whoami
####################
whobei=`whoami`
if [[ $whobei == "root" ]];then SUDO="";else SUDO=`which sudo`;fi

################################
# setup oracle proxy for yum
################################
if [[ $ENABLE_PROXY =~ ^[tT] ]]; then
  PROXY=$proxy
  if [[ $(grep -c proxy $yum_conf) == 0 ]]; then
      echo "Adding proxy $proxy to $yum_conf"
      $SUDO sed -ie "\$a$proxy" $yum_conf
  fi
  export http_proxy=$proxy
  export https_proxy=$proxy
  #printf -v no_proxy '%s,' 172.31.2.{1..255};
  export no_proxy="localhost,127.0.0.1,us.oracle.com,$MASTER_REPO"

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
$SUDO sed -i "s/\/home\/<USER>/\/$whobei/g" /etc/systemd/system/vncserver@.service
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
alias ll='ls -lh --color'
EOF

if [[ $ENABLE_PROXY =~ ^[tT] ]]; then
cat >> ~/.bashrc << EOF
export http_proxy=$proxy
export https_proxy=$proxy
export no_proxy="localhost,127.0.0.1,us.oracle.com,$no_proxy,$MASTER_REPO"
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
#sleep 60

echo "Removing packages not needed"
  $SUDO systemctl disable firewalld
  $SUDO iptables -F
  $SUDO yum --enablerepo=epel,ol7_optional_latest -y remove $package_remove_list

echo "Installing package list"
  $SUDO yum clean all
  $SUDO yum --enablerepo=epel,ol7_latest,ol7_optional_latest -y install $package_list


echo "Installing createrepo rpm"
  $SUDO yum --enablerepo=ol7_latest -y install createrepo

echo "Downloading extra packages from RDO EPEL ... this can take few minutes"
  $SUDO mkdir -p /var/lib/repos/rdolocal/$OPENSTACK_RELEASE

  size=$(du -sm /var/lib/repos/rdolocal/$OPENSTACK_RELEASE|awk '{print $1}')
  if [[ $size -lt 240 ]] ; then
    \rm -rf /var/lib/repos/rdolocal/$OPENSTACK_RELEASE
    $SUDO wget  -nd -q -P /var/lib/repos/rdolocal/$OPENSTACK_RELEASE -r --no-parent ${MASTER_REPO}/rdolocal/${OPENSTACK_RELEASE}/

#  $SUDO cat ./packages.list | while read rpm ; do
#          /usr/bin/yum  -y install --downloaddir=/var/lib/repos/rdolocal --downloadonly $rpm | grep Installed || \
#          /usr/bin/yum  -y reinstall --downloaddir=/var/lib/repos/rdolocal --downloadonly $rpm
#        done
    $SUDO createrepo /var/lib/repos/rdolocal/$OPENSTACK_RELEASE
    $SUDO cat > /etc/yum.repos.d/rdolocal.repo << EOF
[rdolocal]
baseurl = file:///rdolocal/$OPENSTACK_RELEASE
enabled = 1
gpgcheck = 0
name = local rdolocal repo for $OPENSTACK_RELEASE
priority = 1
EOF
  fi

  $SUDO sed -i "s/enabled=1/enabled=0/g" /etc/yum.repos.d/*
  $SUDO cd /
  if [[ ! -h /rdolocal ]] ; then
    $SUDO ln -s /var/lib/repos/rdolocal rdolocal
  fi

echo "Installing package list"
  $SUDO yum clean all
  $SUDO yum --enablerepo=rdolocal -y install $package_list

echo "Exporting local repo /var/lib/repos"
  $SUDO grep "/var/lib/repos " /etc/exports || echo "/var/lib/repos      *(ro,async)" >> /etc/exports
  $SUDO /sbin/exportfs -av


################################
# pip install 
################################
echo "PIP: Installing ansible and shade"
if [[ $ENABLE_PROXY =~ ^[tT] ]]; then
  $SUDO pip --proxy $PROXY install ansible==2.1.1
  $SUDO pip --proxy $PROXY install shade
else
  $SUDO pip install ansible==2.1.1
  $SUDO pip install shade
fi

source ~/.bashrc
