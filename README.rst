=============
micropg
=============

A MicroPython PostgreSQL database driver.


Installation
-----------------

use upip 
::

    $ micropytohn -m upip install micropg

copy a module file.
::

    $ cd $(HOME)/.micropython/lib
    $ wget https://github.com/nakagami/micropg/raw/master/micropg.py

Example
-----------------

Query::

   import micropg
   conn = micropg.connect(host='localhost',
                       user='postgres',
                       password='secret',
                       database='database_name')
   cur = conn.cursor()
   cur.execute('select foo, bar from baz')
   for r in cur.fetchall():
      print(r[0], r[1])
   conn.close()

