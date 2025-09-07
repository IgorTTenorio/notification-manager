import os

class BaseDir:
	def get():
		return os.path.realpath(__file__).replace("\\util\\basedir.py", "")