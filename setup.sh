#!/usr/bin/env bash

pip install -r requirements.txt
python dbCreate.py
python dbMigrate.py
python seed.py
