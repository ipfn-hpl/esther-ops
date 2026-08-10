import sys
import os
# sys.path.insert(0, '/var/www/esther-ops/check-list/flask')

PATH=os.path.dirname(__file__)
sys.path.insert(0, PATH)
from check_list_app import app as application

# for test use:
#application.run(debug=True)
#application.run()
