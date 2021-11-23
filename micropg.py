#############################################################################
# The MIT License (MIT)
#
# Copyright (c) 2014-2019, 2021 Hajime Nakagami
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
##############################################################################
# PostgreSQL driver for micropython https://github.com/micropython/micropython
# It's a minipg (https://github.com/nakagami/minipg) subset.
import ssl
import hashlib
import socket
import binascii
import random

VERSION = (0, 3, 0)
__version__ = '%s.%s.%s' % VERSION
apilevel = '2.0'
threadsafety = 1
paramstyle = 'format'

# -----------------------------------------------------------------------------
# http://www.postgresql.org/docs/9.6/static/protocol.html
# http://www.postgresql.org/docs/9.6/static/protocol-message-formats.html

# https://github.com/postgres/postgres/blob/master/src/include/catalog/pg_type.h
PG_TYPE_BOOL = 16
PG_TYPE_BYTEA = 17
PG_TYPE_CHAR = 18
PG_TYPE_NAME = 19
PG_TYPE_INT8 = 20
PG_TYPE_INT2 = 21
PG_TYPE_INT2VECTOR = 22
PG_TYPE_INT4 = 23
PG_TYPE_REGPROC = 24
PG_TYPE_TEXT = 25
PG_TYPE_OID = 26
PG_TYPE_TID = 27
PG_TYPE_XID = 28
PG_TYPE_CID = 29
PG_TYPE_VECTOROID = 30
PG_TYPE_JSON = 114
PG_TYPE_XML = 142
PG_TYPE_PGNODETREE = 194
PG_TYPE_POINT = 600
PG_TYPE_LSEG = 601
PG_TYPE_PATH = 602
PG_TYPE_BOX = 603
PG_TYPE_POLYGON = 604
PG_TYPE_LINE = 628
PG_TYPE_FLOAT4 = 700
PG_TYPE_FLOAT8 = 701
PG_TYPE_ABSTIME = 702
PG_TYPE_RELTIME = 703
PG_TYPE_TINTERVAL = 704
PG_TYPE_UNKNOWN = 705
PG_TYPE_CIRCLE = 718
PG_TYPE_CASH = 790
PG_TYPE_MACADDR = 829
PG_TYPE_INET = 869
PG_TYPE_CIDR = 650
PG_TYPE_BOOLARRAY = 1000
PG_TYPE_NAMEARRAY = 1003
PG_TYPE_INT2ARRAY = 1005
PG_TYPE_INT4ARRAY = 1007
PG_TYPE_TEXTARRAY = 1009
PG_TYPE_VARCHARARRAY = 1015
PG_TYPE_FLOAT4ARRAY = 1021
PG_TYPE_ARRAYOID = 1028
PG_TYPE_ACLITEM = 1033
PG_TYPE_BPCHAR = 1042
PG_TYPE_VARCHAR = 1043
PG_TYPE_DATE = 1082
PG_TYPE_TIME = 1083
PG_TYPE_TIMESTAMP = 1114
PG_TYPE_TIMESTAMPTZ = 1184
PG_TYPE_INTERVAL = 1186
PG_TYPE_CSTRINGARRAY = 1263
PG_TYPE_TIMETZ = 1266
PG_TYPE_BIT = 1560
PG_TYPE_VARBIT = 1562
PG_TYPE_NUMERIC = 1700
PG_TYPE_REFCURSOR = 1790
PG_TYPE_REGPROCEDURE = 2202
PG_TYPE_REGOPER = 2203
PG_TYPE_REGOPERATOR = 2204
PG_TYPE_REGCLASS = 2205
PG_TYPE_REGTYPE = 2206
PG_TYPE_REGTYPEARRAY = 2211
PG_TYPE_UUID = 2950
PG_TYPE_TSVECTOR = 3614
PG_TYPE_GTSVECTOR = 3642
PG_TYPE_TSQUERY = 3615
PG_TYPE_REGCONFIG = 3734
PG_TYPE_REGDICTIONARY = 3769
PG_TYPE_INT4RANGE = 3904
PG_TYPE_RECORD = 2249
PG_TYPE_RECORDARRAY = 2287
PG_TYPE_CSTRING = 2275
PG_TYPE_ANY = 2276
PG_TYPE_ANYARRAY = 2277
PG_TYPE_VOID = 2278
PG_TYPE_TRIGGER = 2279
PG_TYPE_EVTTRIGGER = 3838
PG_TYPE_LANGUAGE_HANDLER = 2280
PG_TYPE_INTERNAL = 2281
PG_TYPE_OPAQUE = 2282
PG_TYPE_ANYELEMENT = 2283
PG_TYPE_ANYNONARRAY = 2776
PG_TYPE_ANYENUM = 3500
PG_TYPE_FDW_HANDLER = 3115
PG_TYPE_JSONBOID = 3802
PG_TYPE_ANYRANGE = 3831


def hmac_sha256_digest(key, msg):
    pad_key = key + b'\x00' * (64 - (len(key) % 64))
    ik = bytes([0x36 ^ b for b in pad_key])
    ok = bytes([0x5c ^ b for b in pad_key])
    return hashlib.sha256(ok + hashlib.sha256(ik+msg).digest()).digest()


def pbkdf2_hmac_sha256(password_bytes, salt, iterations):
    # hashlib.pbkdf2_hmac('sha256', password_bytes, salt, iterations)
    _u1 = hmac_sha256_digest(password_bytes, salt+b'\x00\x00\x00\x01')

    _ui = int.from_bytes(_u1, 'big')

    for _ in range(iterations - 1):
        _u1 = hmac_sha256_digest(password_bytes, _u1)
        _ui ^= int.from_bytes(_u1, 'big')

    return _ui.to_bytes(32, 'big')


def _decode_column(data, oid, encoding):
    def _parse_point(data):
        x, y = data[1:-1].split(',')
        return (float(x), float(y))

    if data is None:
        return data
    data = data.decode(encoding)
    if oid in (PG_TYPE_BOOL,):
        return data == 't'
    elif oid in (PG_TYPE_INT2, PG_TYPE_INT4, PG_TYPE_INT8, PG_TYPE_OID,):
        return int(data)
    elif oid in (PG_TYPE_FLOAT4, PG_TYPE_FLOAT8):
        return float(data)
    elif oid in (PG_TYPE_BYTEA, ):
        assert data[:2] == u'\\x'
        hex_str = data[2:]
        ia = [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]
        return bytes(ia)
    elif oid in (PG_TYPE_CHAR, PG_TYPE_TEXT, PG_TYPE_BPCHAR, PG_TYPE_VARCHAR, PG_TYPE_NAME, PG_TYPE_JSONBOID, PG_TYPE_XML):
        return data
    elif oid in (PG_TYPE_UNKNOWN, PG_TYPE_PGNODETREE, PG_TYPE_TSVECTOR, PG_TYPE_INET):
        return data
    elif oid in (PG_TYPE_INT2ARRAY, PG_TYPE_INT4ARRAY):
        return [int(i) for i in data[1:-1].split(',')]
    elif oid in (PG_TYPE_NAMEARRAY, PG_TYPE_TEXTARRAY):
        return [s for s in data[1:-1].split(',')]
    elif oid in (PG_TYPE_FLOAT4ARRAY, ):
        return [float(f) for f in data[1:-1].split(',')]
    elif oid in (PG_TYPE_INT2VECTOR, ):
        return [int(i) for i in data.split(' ')]
    elif oid in (PG_TYPE_POINT, ):
        return _parse_point(data)
    elif oid in (PG_TYPE_CIRCLE, ):
        p = data[1:data.find(')')+1]
        r = data[len(p)+2:-1]
        return (_parse_point(p), float(r))
    elif oid in (PG_TYPE_LSEG, PG_TYPE_PATH, PG_TYPE_BOX, PG_TYPE_POLYGON, PG_TYPE_LINE):
        return eval(data)
    return data


def _bytes_to_bint(b):      # Read as big endian
    r = 0
    for n in b:
        r = r * 256 + n
    return r


def _bint_to_bytes(val):    # Convert int value to big endian 4 bytes.
    return bytes([(val >> 24) & 0xff, (val >> 16) & 0xff, (val >> 8) & 0xff, val & 0xff])


def _bytes_to_int(b):       # Read as little endian
    r = 0
    for n in reversed(b):
        r = r * 256 + n
    return r


def _int_to_bytes(val):    # Convert int value to little endian 4 bytes.
    return bytes([val & 0xff, (val >> 8) & 0xff, (val >> 16) & 0xff, (val >> 24) & 0xff])


class Error(Exception):
    def __init__(self, *args):
        super(Error, self).__init__(*args)
        if len(args) > 0:
            self.message = args[0]
        else:
            self.message = b'Database Error'
        if len(args) > 1:
            self.code = args[1]
        else:
            self.code = ''

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.code + ":" + self.message


class Warning(Exception):
    pass


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class InternalError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class DataError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    def __init__(self):
        DatabaseError.__init__(self, 'NotSupportedError')


class Cursor(object):
    def __init__(self, connection):
        self.connection = connection
        self.description = []
        self._rows = []
        self._rowcount = 0
        self.arraysize = 1
        self.query = None

    def __enter__(self):
        return self

    def __exit__(self, exc, value, traceback):
        self.close()

    def callproc(self, procname, args=()):
        raise NotSupportedError()

    def nextset(self, procname, args=()):
        raise NotSupportedError()

    def setinputsizes(sizes):
        pass

    def setoutputsize(size, column=None):
        pass

    def execute(self, query, args=()):
        if not self.connection or not self.connection.is_connect():
            raise ProgrammingError(u"08003:Lost connection")
        self.description = []
        self._rows.clear()
        self.args = args
        if args:
            escaped_args = tuple(
                self.connection.escape_parameter(arg).replace(u'%', u'%%') for arg in args
            )
            query = query.replace(u'%', u'%%').replace(u'%%s', u'%s')
            query = query % escaped_args
            query = query.replace(u'%%', u'%')
        self.query = query
        self.connection.execute(query, self)

    def executemany(self, query, seq_of_params):
        rowcount = 0
        for params in seq_of_params:
            self.execute(query, params)
            rowcount += self._rowcount
        self._rowcount = rowcount

    def fetchone(self):
        if not self.connection or not self.connection.is_connect():
            raise OperationalError(u"08003:Lost connection")
        if len(self._rows):
            r = self._rows[0]
            self._rows = self._rows[1:]
            return r
        return None

    def fetchmany(self, size=1):
        rs = []
        for i in range(size):
            r = self.fetchone()
            if not r:
                break
            rs.append(r)
        return rs

    def fetchall(self):
        r = list(self._rows)
        self._rows.clear()
        return r

    def close(self):
        self.connection = None

    @property
    def rowcount(self):
        return self._rowcount

    @property
    def closed(self):
        return self.connection is None or not self.connection.is_connect()

    def __iter__(self):
        return self

    def __next__(self):
        r = self.fetchone()
        if not r:
            raise StopIteration()
        return r

    def next(self):
        return self.__next__()


class Connection(object):
    def __init__(self, user, password, database, host, port, timeout, use_ssl):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.encoding = 'UTF8'
        self.autocommit = False
        self.server_version = ''
        self._ready_for_query = b'I'
        self.encoders = {}
        self.tz_name = None
        self.tzinfo = None
        self._open()

    def __enter__(self):
        return self

    def __exit__(self, exc, value, traceback):
        self.close()

    def _send_data(self, message, data):
        self._write(b''.join([message, _bint_to_bytes(len(data) + 4), data]))

    def _send_message(self, message, data):
        self._write(b''.join([message, _bint_to_bytes(len(data) + 4), data, b'H\x00\x00\x00\x04']))

    def _process_messages(self, obj):
        errobj = None
        while True:
            try:
                code = ord(self._read(1))
            except OperationalError:
                # something error occured
                break
            ln = _bytes_to_bint(self._read(4)) - 4
            data = self._read(ln)
            if code == 90:
                self._ready_for_query = data
                break
            elif code == 82:
                auth_method = _bytes_to_bint(data[:4])
                if auth_method == 0:      # trust
                    pass
                elif auth_method == 5:    # md5
                    salt = data[4:]
                    h1 = binascii.hexlify(hashlib.md5(self.password.encode('ascii') + self.user.encode("ascii")).digest())
                    h2 = binascii.hexlify(hashlib.md5(h1 + salt).digest())
                    self._send_data(b'p', b''.join([b'md5', h2, b'\x00']))
                    # accept
                    code = ord(self._read(1))
                    assert code == 82
                    ln = _bytes_to_bint(self._read(4)) - 4
                    data = self._read(ln)
                    assert _bytes_to_bint(data[:4]) == 0
                elif auth_method == 10:   # SASL
                    assert data[4:-2].decode('utf-8') == 'SCRAM-SHA-256'
                    printable = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/'
                    client_nonce = ''.join(
                        printable[random.randrange(0, len(printable))]
                        for i in range(24)
                    )

                    # send client first message
                    first_message = 'n,,n=,r=' + client_nonce
                    self._send_data(b'p', b''.join([
                        b'SCRAM-SHA-256\x00',
                        _bint_to_bytes(len(first_message)),
                        first_message.encode('utf-8')
                    ]))

                    code = ord(self._read(1))
                    assert code == 82
                    ln = _bytes_to_bint(self._read(4)) - 4
                    data = self._read(ln)
                    _bytes_to_bint(data[:4]) == 11      # SCRAM first

                    server = {
                        kv[0]: kv[2:]
                        for kv in data[4:].decode('utf-8').split(',')
                    }
                    # r: server nonce
                    # s: servre salt
                    # i: iteration count
                    assert server['r'][:len(client_nonce)] == client_nonce

                    # send client final message
                    salted_pass = pbkdf2_hmac_sha256(
                        self.password.encode('utf-8'),
                        binascii.a2b_base64(server['s']),
                        int(server['i']),
                    )

                    client_key = hmac_sha256_digest(salted_pass, b"Client Key")

                    client_first_message_bare = "n=,r=" + client_nonce
                    server_first_message = "r=%s,s=%s,i=%s" % (server['r'], server['s'], server['i'])
                    client_final_message_without_proof = "c=biws,r=" + server['r']
                    auth_msg = ','.join([
                        client_first_message_bare,
                        server_first_message,
                        client_final_message_without_proof
                    ])

                    client_sig = hmac_sha256_digest(
                        hashlib.sha256(client_key).digest(),
                        auth_msg.encode('utf-8'),
                    )

                    proof = binascii.b2a_base64(
                        b"".join([bytes([x ^ y]) for x, y in zip(client_key, client_sig)])
                    )
                    if proof[-1:] == b'\n':
                        proof = proof[:-1]
                    self._send_data(
                        b'p',
                        (client_final_message_without_proof + ",p=").encode('utf-8') + proof
                    )

                    code = ord(self._read(1))
                    assert code == 82
                    ln = _bytes_to_bint(self._read(4)) - 4
                    data = self._read(ln)
                    _bytes_to_bint(data[:4]) == 12      # SCRAM final

                    # accept
                    code = ord(self._read(1))
                    assert code == 82
                    ln = _bytes_to_bint(self._read(4)) - 4
                    data = self._read(ln)
                    assert _bytes_to_bint(data[:4]) == 0
                else:
                    errobj = InterfaceError("Authentication method %d not supported." % (auth_method,))
            elif code == 83:
                k, v, _ = data.split(b'\x00')
                if k == b'server_encoding':
                    self.encoding = v.decode('ascii')
                elif k == b'server_version':
                    version = v.decode('ascii').split('(')[0].split('.')
                    self.server_version = int(version[0]) * 10000
                    if len(version) > 0:
                        try:
                            self.server_version += int(version[1]) * 100
                        except Exception:
                            pass
                    if len(version) > 1:
                        try:
                            self.server_version += int(version[2])
                        except Exception:
                            pass
                elif k == b'TimeZone':
                    self.tz_name = v.decode('ascii')
                    self.tzinfo = None
            elif code == 75:
                pass
            elif code == 67:
                if not obj:
                    continue
                command = data[:-1].decode('ascii')
                if command == 'SHOW':
                    obj._rowcount = 1
                else:
                    for k in ('SELECT', 'UPDATE', 'DELETE', 'INSERT'):
                        if command[:len(k)] == k:
                            obj._rowcount = int(command.split(' ')[-1])
                            break
            elif code == 84:
                if not obj:
                    continue
                count = _bytes_to_bint(data[0:2])
                obj.description = [None] * count
                n = 2
                idx = 0
                for i in range(count):
                    name = data[n:n+data[n:].find(b'\x00')]
                    n += len(name) + 1
                    try:
                        name = name.decode(self.encoding)
                    except UnicodeDecodeError:
                        pass
                    type_code = _bytes_to_bint(data[n+6:n+10])
                    if type_code == PG_TYPE_VARCHAR:
                        size = _bytes_to_bint(data[n+12:n+16]) - 4
                        precision = -1
                        scale = -1
                    elif type_code == PG_TYPE_NUMERIC:
                        size = _bytes_to_bint(data[n+10:n+12])
                        precision = _bytes_to_bint(data[n+12:n+14])
                        scale = precision - _bytes_to_bint(data[n+14:n+16])
                    else:
                        size = _bytes_to_bint(data[n+10:n+12])
                        precision = -1
                        scale = -1
#                        table_oid = _bytes_to_bint(data[n:n+4])
#                        table_pos = _bytes_to_bint(data[n+4:n+6])
#                        size = _bytes_to_bint(data[n+10:n+12])
#                        modifier = _bytes_to_bint(data[n+12:n+16])
#                        format = _bytes_to_bint(data[n+16:n+18]),
                    field = (name, type_code, None, size, precision, scale, None)

                    n += 18
                    obj.description[idx] = field
                    idx += 1
            elif code == 68:
                if not obj:
                    continue
                n = 2
                row = []
                while n < len(data):
                    if data[n:n+4] == b'\xff\xff\xff\xff':
                        row.append(None)
                        n += 4
                    else:
                        ln = _bytes_to_bint(data[n:n+4])
                        n += 4
                        row.append(data[n:n+ln])
                        n += ln
                for i in range(len(row)):
                    row[i] = _decode_column(row[i], obj.description[i][1], self.encoding)
                obj._rows.append(tuple(row))
            elif code == 78:
                pass
            elif code == 69 and not errobj:
                err = data.split(b'\x00')
                # http://www.postgresql.org/docs/9.3/static/errcodes-appendix.html
                errcode = err[2][1:]
                message = errcode + b':' + err[3][1:]
                message = message.decode(self.encoding)
                if errcode[:2] == b'0A':
                    errobj = NotSupportedError(message, errcode)
                elif errcode[:2] in (b'20', b'21'):
                    errobj = ProgrammingError(message, errcode)
                elif errcode[:2] in (b'22', ):
                    errobj = DataError(message, errcode)
                elif errcode[:2] == b'23':
                    errobj = IntegrityError(message, errcode)
                elif errcode[:2] in(b'24', b'25'):
                    errobj = InternalError(message, errcode)
                elif errcode[:2] in(b'26', b'27', b'28'):
                    errobj = OperationalError(message, errcode)
                elif errcode[:2] in(b'2B', b'2D', b'2F'):
                    errobj = InternalError(message, errcode)
                elif errcode[:2] == b'34':
                    errobj = OperationalError(message, errcode)
                elif errcode[:2] in (b'38', b'39', b'3B'):
                    errobj = InternalError(message, errcode)
                elif errcode[:2] in (b'3D', b'3F'):
                    errobj = ProgrammingError(message, errcode)
                elif errcode[:2] in (b'40', b'42', b'44'):
                    errobj = ProgrammingError(message, errcode)
                elif errcode[:1] == b'5':
                    errobj = OperationalError(message, errcode)
                elif errcode[:1] in b'F':
                    errobj = InternalError(message, errcode)
                elif errcode[:1] in b'H':
                    errobj = OperationalError(message, errcode)
                elif errcode[:1] in (b'P', b'X'):
                    errobj = InternalError(message, errcode)
                else:
                    errobj = DatabaseError(message, errcode)
            elif code == 72:    # CopyOutputResponse('H')
                pass
            elif code == 100:   # CopyData('d')
                obj.write(data)
            elif code == 99:    # CopyDataDone('c')
                pass
            elif code == 71:    # CopyInResponse('G')
                while True:
                    buf = obj.read(8192)
                    if not buf:
                        break
                    # send CopyData
                    self._write(b'd' + _bint_to_bytes(len(buf) + 4))
                    self._write(buf)
                # send CopyDone and Sync
                self._write(b'c\x00\x00\x00\x04S\x00\x00\x00\x04')
            else:
                pass
        return errobj

    def process_messages(self, obj):
        err = self._process_messages(obj)
        if err:
            raise err

    def _read(self, ln):
        if not self.sock:
            raise OperationalError(u"08003:Lost connection")
        r = b''
        while len(r) < ln:
            if hasattr(self.sock, "read"):
                b = self.sock.read(ln-len(r))
            else:
                b = self.sock.recv(ln-len(r))
            if not b:
                raise OperationalError(u"08003:Can't recv packets")
            r += b
        return r

    def _write(self, b):
        if not self.sock:
            raise OperationalError(u"08003:Lost connection")
        n = 0
        while (n < len(b)):
            if hasattr(self.sock, "write"):
                n += self.sock.write(b[n:])
            else:
                n += self.sock.send(b[n:])

    def _open(self):
        self.sock = socket.socket()
        self.sock.connect(socket.getaddrinfo(self.host, self.port)[0][-1])

        if self.timeout is not None:
            self.sock.settimeout(float(self.timeout))

        if self.use_ssl:
            self._write(_bint_to_bytes(8))
            self._write(_bint_to_bytes(80877103))    # SSL request
            if self._read(1) == b'S':
                self.sock = ssl.wrap_socket(self.sock)
            else:
                raise InterfaceError("Server refuses SSL")

        # protocol version 3.0
        v = b'\x00\x03\x00\x00'
        v += b'user\x00' + self.user.encode('ascii') + b'\x00'
        if self.database:
            v += b'database\x00' + self.database.encode('ascii') + b'\x00'
        v += b'\x00'

        self._write(_bint_to_bytes(len(v) + 4) + v)
        self.process_messages(None)

    def escape_parameter(self, v):
        t = type(v)
        func = self.encoders.get(t)
        if func:
            return func(self, v)
        if v is None:
            return 'NULL'
        elif t == str:  # string
            return u"'" + v.replace(u"'", u"''") + u"'"
        elif t == bytearray or t == bytes:        # binary
            return "'" + ''.join(['\\%03o' % (c, ) for c in v]) + "'::bytea"
        elif t == bool:
            return u"TRUE" if v else u"FALSE"
        elif t == list or t == tuple:
            return u'ARRAY[' + u','.join([self.escape_parameter(e) for e in v]) + u']'
        else:
            return "'" + str(v) + "'"

    @property
    def is_dirty(self):
        return self._ready_for_query in b'TE'

    def is_connect(self):
        return bool(self.sock)

    def cursor(self):
        return Cursor(self)

    def _execute(self, query, obj):
        self._send_message(b'Q', query.encode(self.encoding) + b'\x00')
        self.process_messages(obj)
        if self.autocommit:
            self.commit()

    def execute(self, query, obj=None):
        if self._ready_for_query != b'T':
            self.begin()
        self._execute(query, obj)

    @property
    def isolation_level(self):
        return self.get_parameter_status('TRANSACTION ISOLATION LEVEL')

    def set_autocommit(self, autocommit):
        self.autocommit = autocommit

    def _begin(self):
        self._send_message(b'Q', b"BEGIN\x00")
        self._process_messages(None)

    def begin(self):
        if self._ready_for_query == b'E':
            self._rollback()
        self._begin()

    def commit(self):
        if self.sock:
            self._send_message(b'Q', b"COMMIT\x00")
            self.process_messages(None)
            self._begin()

    def _rollback(self):
        if self.sock:
            self._send_message(b'Q', b"ROLLBACK\x00")
            self.process_messages(None)

    def rollback(self):
        self._rollback()
        self.begin()

    def reopen(self):
        self.close()
        self._open()

    def close(self):
        if self.sock:
            # send Terminate
            self._write(b'X\x00\x00\x00\x04')
            self.sock.close()
            self.sock = None


def connect(host, user, password='', database=None, port=None, timeout=None, use_ssl=False):
    return Connection(user, password, database, host, port if port else 5432, timeout, use_ssl)
