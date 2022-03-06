#! /bin/bash

for version in "3.6" "3.7" "3.8" "3.9" "3.10"; do
	img="python:$version-alpine"

	sudo docker pull "$img" \
		&& sudo docker run \
			-it \
			--rm \
			-v "$(pwd):/mnt" \
			-w /mnt \
			"$img" \
			python3 ./setup.py bdist_egg \
		|| exit
done

sudo chown -R "$(id -u):$(id -g)" build dist RcData.egg-info
