=============
micropg
=============

PostgreSQL database driver for Python and MicroPython.


Installation
-----------------

Python
+++++++++++++++

::

   pip install micropg

MicroPython
+++++++++++++++

Go interactive shell and install with mip as follow.
::

   >>> import mip
   >>> mip.install("https://github.com/nakagami/micropg/blob/master/micropg.py")

Example
-----------------
You find more examples in the `examples <https://github.com/nakagami/micropg/tree/master/examples>`_ folder.

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

- If installed in Python, it can only handle types supported by MicroPython.
- Supported Authentication METHOD are only 'trust', 'md5' and 'scram-sha-256'.
- Not support for array data types.
- Not support for prepared statements.

If you use md5 authentication METHOD, you may need a patch
https://github.com/nakagami/micropg/issues/2



For CPython
---------------------

I also wrote a pure Python driver.
https://github.com/nakagami/minipg
