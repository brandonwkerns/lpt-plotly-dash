#!/var/www/FLASKAPPS/lpt/venv/bin/python3
import sys
sys.path.insert(0,"/var/www/FLASKAPPS")
print('Python executable: ', sys.executable)
print('Python environment: ', sys.prefix)

## Set cache dir for Numba.
import os
import getpass
whoami = getpass.getuser()

## If this is running as user 'www-data', it is a production run.
## and it needs to use the directory with permissions for www-data.
## Otherwise, it is developing/testing, and uses a directory with
## permissions for the local user.
#if whoami == 'www-data':
#   os.environ['NUMBA_CACHE_DIR']='/var/www/FLASKAPPS/lpt/numba_cache'
#else:
#   os.environ['NUMBA_CACHE_DIR']='/var/www/FLASKAPPS/lpt/numba_cache_testing'


#import logging
#logging.basicConfig(level=logging.DEBUG, filename='/var/www/FLASKAPPS/lpt/lpt.log')

from lpt.app import server as application

