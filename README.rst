=============
micropg
=============

A MicroPython PostgreSQL database driver.


Installation
-----------------

use upip 
::

    $ micropython -m upip install micropg

or

copy a module file.
::

    $ cd $(HOME)/.micropython/lib
    $ wget https://github.com/nakagami/micropg/raw/master/micropg.py

Example
-----------------

Query::

   import micropg
   conn = micropg.connect(host='127.0.0.1',
                       user='postgres',
                       password='secret',
                       database='database_name',
                       use_ssl=False)
   cur = conn.cursor()
   cur.execute('select foo, bar from baz')
   for r in cur.fetchall():
      print(r[0], r[1])
   conn.close()

Restriction
-----------------

Suport trust and md5 authenticaton methods, not SCRAM-SHA-256 authentication method.

