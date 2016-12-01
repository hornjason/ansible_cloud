

if [[ -z $2 ]]; then
  echo "Must Specify iso image"
  exit
fi

mkdir -p /test
mount_dir=/test
iso="$2"
iso_name=`echo $iso|awk -F'.iso' '{print $1}'`
# create dump_dir
dump_dir="$PWD/$iso_name"

case "$1" in
  dump)
        mount $iso $mount_dir
        mkdir $dump_dir
        # extract files
        cd $mount_dir;tar cf - . |  (cd $dump_dir; tar xfp -);cd -
        umount $mount_dir
        ;;
 cr*)
        # change ks.cfg and update isolinux/isolinux.cfg boot menu if needed
        echo "IM HERE"
        #iso_name="$2"
        cd ./$iso_name
	mkisofs -o ../${iso_name}.iso -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -v -T .
        ;;
esac
