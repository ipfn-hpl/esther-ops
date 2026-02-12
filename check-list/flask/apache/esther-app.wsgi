#!/usr/bin/python3
import sys
import os
import logging

PWD='/var/www/check_list_app'
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, PWD)

# Activate virtual environment
activate_this = PWD  + '/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from check_list_app import app as application
