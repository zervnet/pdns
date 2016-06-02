import json
import time
import unittest
from copy import deepcopy
from pprint import pprint
import subprocess

from test_helper import ApiTestCase

class Cryptokeys(ApiTestCase):
    zone = "cryptokeyzone"
    def setUp(self):
        super(Cryptokeys, self).setUp()
        subprocess.call(["../pdns/pdnsutil", "--config-dir=.", "create-zone", self.zone])

    def test_delete(self):
        subprocess.call(["../pdns/pdnsutil", "--config-dir=.", "add-zone-key", self.zone, "ksk"])
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/2"))
        try:
            out=subprocess.check_output(["../pdns/pdnsutil", "--config-dir=.", "list-keys", self.zone])
            print out
            self.assertFalse(self.zone in out)
        except subprocess.CalledProcessError as e:
            self.fail("pdnsutil list-keys failed: "+e.output)

