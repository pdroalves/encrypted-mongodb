#!/bin/bash
#
sizes=(100 1000 10000 100000)
for size in ${sizes[@]};do
	python synthetic_dataset.py $size
	python load_dataset.py
done
