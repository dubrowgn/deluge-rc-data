#! /bin/bash

for version in "3.6" "3.7" "3.8" "3.9" "3.10-rc"; do
	sudo docker run \
		-it \
		--rm \
		-v "$(pwd):/mnt" \
		-w /mnt \
		"python:$version-alpine" \
		python3 ./setup.py bdist_egg
done
