import sys
import os

PWD = = os.getcwd()
# print(PWD)
sys.path.insert(0, PWD + '/flask-venv/lib/python3.11/site-packages')
sys.path.insert(1, PWD)

from check_list_app import app as application

