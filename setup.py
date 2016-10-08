import sys
sys.path.pop(0)
from setuptools import setup


setup(name='micropg',
      version='0.1.0',
      description='PostgreSQL database driver for  MicroPython',
      long_description='This is a module ported from minipg',
      url='https://github.com/nakagami/micropg',
      author='Hajime Nakagami',
      author_email='nakagami@gmail.com',
      license='MIT',
      py_modules=['micropg'])
