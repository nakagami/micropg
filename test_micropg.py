import micropg

conn = micropg.connect(
    host='127.0.0.1', user='postgres', password='password', database='test_micropg'
)

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
        name varchar(20)
    )
""")

cur.execute("INSERT INTO test_micropg(id, name) values (1, 'test')")
cur.execute("INSERT INTO test_micropg(id, name) values (%s, %s)", [2, 'test2'])

conn.commit()

cur.execute("SELECT id, name FROM test_micropg")
assert cur.fetchall() == [(1, "test"), (2, "test2")]

conn.close()


# test ssl connection

# conn = micropg.connect(
#     host='127.0.0.1', user='postgres', password='password', database='test_micropg', use_ssl=True
# )
# cur = conn.cursor()
# cur.execute("SELECT id, name FROM test_micropg")
# assert cur.fetchall() == [(1, "test"), (2, "test2")]
#
# conn.close()
