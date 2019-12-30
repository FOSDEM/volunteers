#!/bin/bash


echo "Do not forget to create an Edition in the UI first."

python manage.py import_init_data
python manage.py sync_with_penta
