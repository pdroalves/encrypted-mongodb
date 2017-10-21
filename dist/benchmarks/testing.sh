#!/bin/bash
#
sizes=(100 1000 10000 100000 1000000)
# sizes=(1000 10E 000)
for size in ${sizes[@]};do
	if [ ! -f "synthetic_dataset_$size.json" ];then
		python generate_dataset.py $size
		cp "synthetic_dataset.json" "synthetic_dataset_$size.json"
	else
		cp "synthetic_dataset_$size.json" "synthetic_dataset.json"
	fi
		
	echo "Running for $size records"
	# pytest testing.py --benchmark-warmup=on --benchmark-save=$size --benchmark-calibration-precision=100 --benchmark-min-rounds=4000 --benchmark-disable-gc
	python load_dataset.py
	rm "synthetic_dataset.json"
done
