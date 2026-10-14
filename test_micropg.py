import micropg

try:
    micropg.create_database(
        host='127.0.0.1', user='postgres', password='password', database='test_micropg'
    )
except Exception:
    pass

conn = micropg.connect(
    host='127.0.0.1', user='postgres', password='password', database='test_micropg'
)

# server_version and parameter_statuses
assert isinstance(conn.server_version, int) and conn.server_version > 0
assert conn.get_parameter_status('server_version') is not None
_ = conn.isolation_level

cur = conn.cursor()

# error
try:
    cur.execute("BAD STATEMENT")
except micropg.ProgrammingError as e:
    assert e.message == '42601:syntax error at or near "BAD"'


# create table, insert, select
try:
    cur.execute("DROP TABLE test_micropg")
except:
    pass
cur.execute("""
    CREATE TABLE test_micropg(
        id integer,
        name varchar(20),
        val double precision
    )
""")

cur.execute("INSERT INTO test_micropg(id, name, val) values (1, 'test', 1.5)")
assert cur.rowcount == 1
cur.execute("INSERT INTO test_micropg(id, name, val) values (%s, %s, %s)", [2, 'test2', 2.5])
assert cur.rowcount == 1

conn.commit()

cur.execute("SELECT id, name, val FROM test_micropg WHERE id = %s", [1])
assert cur.fetchall() == [(1, "test", 1.5)]

cur.execute("UPDATE test_micropg SET name = 'updated' WHERE id = 1")
assert cur.rowcount == 1

cur.execute("DELETE FROM test_micropg WHERE id = 2")
assert cur.rowcount == 1

conn.commit()

conn.close()

# autocommit test
conn = micropg.connect(
    host='127.0.0.1', user='postgres', password='password', database='test_micropg'
)
conn.set_autocommit(True)
cur = conn.cursor()
cur.execute("VACUUM")
cur.execute("SELECT id, name FROM test_micropg")
assert cur.fetchall() == [(1, "updated")]
conn.close()

if False:   # disable ssl connection
    # test ssl connection
    conn = micropg.connect(
        host='127.0.0.1', user='postgres', password='password', database='test_micropg', use_ssl=True
    )
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM test_micropg")
    assert cur.fetchall() == [(1, "test"), (2, "test2")]

    conn.close()
