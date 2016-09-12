
fullnet(){
ping='fping -c1 -t100 '
echo ping the full network
for n in 2 3 ; do
	for b in $(seq 0 254) ; do
		$ping 10.133.${n}.${b}  >/dev/null 2>&1 && echo "$ping 10.133.${n}.${b} ok" || echo "$ping 10.133.${n}.${b} FAIL"
	done
done
}

pubnet(){
echo ping public network
for i in $(seq 131 169) ; do
	ping -c 1 10.133.1.${i} >/dev/null 2>&1 && echo $i ok || echo $i FAIL
done
}

intvlan(){
for n in 16 30 ; do
	echo ---
	echo ping $n network
	for c in $(seq 0 3); do
		for b in $(seq 0 9); do
			ping -c 1 172.${n}.${c}.11${b} >/dev/null 2>&1 && echo "ping -c 1 172.${n}.${c}.11${b} - net=$n c0${c}b0${b} ok" || echo "ping -c 1 172.${n}.${c}.11${b} - net=$n c0${c}b0${b} FAIL"
		done
	done
done
}

zfs(){
# ping ZFS
ping='fping -c1 -t100 '
for c in $(seq 0 3) ; do
    for h in $(seq 247 250) ; do
        z=172.31.${c}.${h}
        ${ping} ${z} >/dev/null 2>&1 && echo $z ok || echo $z FAIL
    done
done
}

zfs
