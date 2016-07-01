from datetime import datetime
import os
import requests
import urlparse
import unittest
import sqlite3

DAEMON = os.environ.get('DAEMON', 'authoritative')
SQLITE_DB = os.environ.get('SQLITE_DB', 'pdns.sqlite3')


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        # TODO: config
        self.server_address = '127.0.0.1'
        self.server_port = int(os.environ.get('WEBPORT', '5580'))
        self.server_url = 'http://%s:%s/' % (self.server_address, self.server_port)
        self.session = requests.Session()
        self.session.headers = {'X-API-Key': os.environ.get('APIKEY', 'changeme-key'), 'Origin': 'http://%s:%s' % (self.server_address, self.server_port)}

    def url(self, relative_url):
        return urlparse.urljoin(self.server_url, relative_url)

    def assert_success_json(self, result):
        try:
            result.raise_for_status()
        except:
            print result.content
            raise
        self.assertEquals(result.headers['Content-Type'], 'application/json')

    def assert_error_json(self, result):
        self.assertTrue(400 <= result.status_code < 600, "Response has not an error code "+str(result.status_code))
        self.assertEquals(result.headers['Content-Type'], 'application/json', "Response status code "+str(result.status_code))

    def assert_success(self, result):
        try:
            result.raise_for_status()
        except:
            print result.content
            raise


def unique_zone_name():
    return 'test-' + datetime.now().strftime('%d%H%S%M%f') + '.org.'


def is_auth():
    return DAEMON == 'authoritative'


def is_recursor():
    return DAEMON == 'recursor'


def get_auth_db():
    """Return Connection to Authoritative backend DB."""
    return sqlite3.Connection(SQLITE_DB)


def get_db_records(zonename, qtype):
    with get_auth_db() as db:
        rows = db.execute("""
            SELECT name, type, content, ttl
            FROM records
            WHERE type = ? AND domain_id = (
                SELECT id FROM domains WHERE name = ?
            )""", (qtype, zonename.rstrip('.'))).fetchall()
        recs = [{'name': row[0], 'type': row[1], 'content': row[2], 'ttl': row[3]} for row in rows]
        print "DB Records:", recs
        return recs
