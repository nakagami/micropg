import sys
import micropg
from distutils.core import setup

description='PostgreSQL database driver for MicroPython'
setup(name='micropg',
      version="%d.%d.%d" % __import__('micropg').VERSION,
      description=description,
      long_description=description+"""\nThis is a module ported from minipg
https://github.com/nakagami/minipg
""",
      url='https://github.com/nakagami/micropg',
      author='Hajime Nakagami',
      author_email='nakagami@gmail.com',
      license='MIT',
      py_modules=['micropg'])
