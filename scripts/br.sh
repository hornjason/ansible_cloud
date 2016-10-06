#!/bin/bash -x

# Source: http://docs.openstack.org/ops-guide/ops-backup-recovery.html

BACKUPDIR=/var/lib/backup

err (){
    echo verification of openstack failed
}

check_openstack() {
    source ~/keystonerc_admin
    nova flavor-list  || err
    nova agent-list  || err
    nova list || err
    nova availability-zone-list || err
    neutron agent-list || err
    neutron router-list || err
    neutron port-list || err
    glance image-list || err
    ceilometer resource-list || err
    ceilometer sample-list || err
    cinder list || err
    openstack  security group list || err
    heat config-list || err
    ip netns
}

stop_services() {
    openstack-service stop
}

start_services() {
    openstack-service start
}

backup () {
    ID=$(date +%Y%m%d-%H%M)
    if  [  ! -d $BACKUPDIR ] ; then     mkdir -p ${BACKUPDIR} ; fi

    mysqldump --opt --all-databases > ${BACKUPDIR}/openstack.sql.${ID}
    cd /
    \rm ${BACKUPDIR}/backup.tar
    tar rf ${BACKUPDIR}/backup.tar ./${BACKUPDIR}/openstack.sql.${ID}
    for i in aodh ceilometer gnocchi heat horizon httpd keystone nagios neutron nova  rabbitmq swift ; do
        tar rf ${BACKUPDIR}/backup.tar ./var/lib/${i}  ./etc/${i} ./var/log/${i}
    done
    for i in cinder glance ; do
        tar rf ${BACKUPDIR}/backup.tar ./etc/glance ./var/log/glance
    done
        
    tar rf ${BACKUPDIR}/backup.tar ./etc/mongo*
    gzip ${BACKUPDIR}/backup.tar
    mv ${BACKUPDIR}/backup.tar.gz ${BACKUPDIR}/backup.${ID}.tar.gz
    
    # Replicate to another server:
    yum install -y sshpass rsync
    echo "copying backup file: "
    sshpass -p changeme rsync -az --progress ${BACKUPDIR}/backup.${ID}.tar.gz 172.31.254.254:/var/lib/openstack/
}

restore () {
    BckupFile=$1
    if  [  ! -d ${BACKUPDIR} ] ; then     mkdir -p ${BACKUPDIR} ; fi
    yum install -y sshpass rsync
    sshpass -p changeme scp 172.31.254.254:/var/lib/openstack/${BckupFile}  ${BACKUPDIR}/
    echo restoring openstack conf files
    stop_services
    cd /
    tar xzf ${BACKUPDIR}/${BckupFile}
    dbfile=$(tar tzvf $BACKUPDIR/$BckupFile | grep sql | awk '{print $NF}')
    mysql < ${dbfile}
    start_services
}

# backup
# restore backup.20161004-1400.tar.gz
