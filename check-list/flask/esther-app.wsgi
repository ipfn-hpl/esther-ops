import sys
import os

PATH=os.path.dirname(__file__)
print(PATH)

#sys.path.insert(0, '/opt/wsgi/esther-ops/check-list/flask/flask-venv/lib/python3.11/site-packages')
sys.path.insert(0, PATH + '/flask-venv/lib/python3.11/site-packages')
#sys.path.insert(1,'/opt/wsgi/esther-ops/check-list/flask')
sys.path.insert(1, PATH)

from check_list_app import app as application

# for test use:
#application.run(debug=True)
#application.run()
