@ECHO off
TITLE Scoutron Setup and Installer
ECHO "Installing all necessary libraries/APIs"

ECHO "Installing/Upgrading pip"
python -m pip install --upgrade pip

ECHO "Installing/Upgrading numpy"
python -m pip install --upgrade numpy

ECHO "Installing/Upgrading scipy"
python -m pip install --upgrade scipy

ECHO "Installing/Upgrading matplotlib"
python -m pip install --upgrade matplotlib

ECHO "Installing/Upgrading scikit-image"
python -m pip install --upgrade scikit-image

ECHO "Installing/Upgrading Google API client python auth stuff..."
python -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

ECHO "Done!"
PAUSE
