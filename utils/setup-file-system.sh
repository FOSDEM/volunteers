#!/bin/sh
set -o errexit
set -o nounset

mkdir -p logs tool/media/mugshots
sqlite3 volunteers.db
sqlite3 penta.db

