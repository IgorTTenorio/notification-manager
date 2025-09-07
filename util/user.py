import os
import subprocess

class User:
    def get():
        userGUID = os.getlogin()
        userEmail = subprocess.check_output("whoami /upn", shell=True)
        userEmail = userEmail.strip().decode("utf-8")
        return userGUID, userEmail