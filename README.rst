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

   # execute with parameter
   cur.execute('select foo, bar from baz where name=%s ', ['nakagami'])
   for r in cur.fetchall():
      print(r[0], r[1])

   conn.close()

Restrictions and Unsupported Features
--------------------------------------

- Supported Authentication METHOD are only 'trust', 'md5' and 'scram-sha-256'.
- Not support for array data types.
- Not support for prepared statements.

If you use md5 authentication METHOD, you may need a patch
https://github.com/nakagami/micropg/issues/2
