import micropg
conn = micropg.connect(host='127.0.0.1',
                    user='postgres',
                    password='',
                    database='test_micropg')

cur = conn.cursor()
try:
    cur.execute("DROP TABLE test_micropg")
except:
    pass
cur.execute("""
    CREATE TABLE test_micropg(
        id integer,
        name varchar(20)
    )
""")

cur.execute("INSERT INTO test_micropg(id, name) values (1, 'test')")
cur.execute("SELECT id, name FROM test_micropg")
assert cur.fetchall() == [(1, "test")]

conn.close()
