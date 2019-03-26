@ECHO off
TITLE Scoutron Setup and Installer
ECHO "Installing all necessary libraries/APIs"

ECHO "Installing/Upgrading pip"
python -m pip install --upgrade --user pip

ECHO "Installing/Upgrading numpy"
python -m pip install --upgrade --user numpy

ECHO "Installing/Upgrading scipy"
python -m pip install --upgrade --user scipy

ECHO "Installing/Upgrading matplotlib"
python -m pip install --upgrade --user matplotlib

ECHO "Installing/Upgrading scikit-image"
python -m pip install --upgrade --user scikit-image

ECHO "Installing/Upgrading Google API client python auth stuff..."
python -m pip install --upgrade --user google-api-python-client google-auth-httplib2 google-auth-oauthlib

ECHO "Done!"
PAUSE
