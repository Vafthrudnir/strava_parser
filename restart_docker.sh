#!/bin/bash
set -ex

docker stop strava_parser
docker rm strava_parser
./build_docker.sh
./run_docker.sh
