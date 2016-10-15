import sys
sys.path.pop(0)
from distutils.core import setup


setup(name='micropg',
      version="%d.%d.%d" % __import__('micropg').VERSION,
      description='PostgreSQL database driver for MicroPython',
      long_description=description+"""\nThis is a module ported from minipg
https://github.com/nakagami/minipg
""",
      url='https://github.com/nakagami/micropg',
      author='Hajime Nakagami',
      author_email='nakagami@gmail.com',
      license='MIT',
      py_modules=['micropg'])
