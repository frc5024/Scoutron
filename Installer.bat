@echo off
echo "Installing all necessary libraries/APIs"
cd D:\Saves\Python\ScoutingScanner\Portable Python 3.7.0 x64\App\Python
python -m pip install -U pip
python -m pip install -U matplotlib
pip install -U scikit-image
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
echo "Done!"
set /p "Press Enter to exit..."
