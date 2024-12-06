#!/bin/bash
# This skript creates an example database with docker
sudo docker run --restart always -itd -p 5432:5432 --name micropg-testing -e POSTGRES_PASSWORD=123456 postgres