#!/bin/sh

## Build Python environment (venv) for the Dash application.
## Note: The venv MUST be built using the system version of Python 3
##       that mod_wsgi was compiled with (e.g., /usr/bin/python3.7)

PYTHON=/usr/bin/python3.7
VENV_DIR=./venv

## Create venv.
echo "Creating virtual environment using $PYTHON in $VENV_DIR."
$PYTHON -m venv $VENV_DIR

## Install modules to the venv.
echo "Installing modules in $VENV_DIR."
source $VENV_DIR/bin/activate
$VENV_DIR/bin/pip3 install -r requirements.txt


echo "All done."

exit 0

