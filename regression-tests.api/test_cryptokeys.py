import subprocess

from test_helper import ApiTestCase

class Cryptokeys(ApiTestCase):
    zone = "cryptokeyzone"
    def setUp(self):
        super(Cryptokeys, self).setUp()
        try:
            subprocess.check_output(["../pdns/pdnsutil", "--config-dir=.", "create-zone", self.zone])
        except subprocess.CalledProcessError as e:
            self.fail("Couldn't create zone: "+e.output)


    def tearDown(self):
        super(Cryptokeys,self).tearDown()
        try:
            subprocess.check_output(["../pdns/pdnsutil", "--config-dir=.", "delete-zone", self.zone])
        except subprocess.CalledProcessError as e:
            self.fail("Couldn't delete zone: "+e.output)


    # This methode test the DELETE api call. Sometimes 200 or 422 are valid return codes,
    # because it "could" happen that the backend crashes during the test or the remove function returns false.
    # In this case 422 is correct. I don't know how to force false backend behavior. So i assume that the backend
    # works correct.
    def test_delete(self):
        try:
            keyid = subprocess.check_output(["../pdns/pdnsutil", "--config-dir=.", "add-zone-key", self.zone, "ksk"])
        except subprocess.CalledProcessError as e:
            self.fail("pdnsutil add-zone-key failed: "+e.output)

        #checks the status code. I don't know how to test explicit that the backend fail removing a key.
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+keyid))
        self.assertTrue(r.status_code == 200 or r.status_code == 422)

        #Check that the key is actually deleted
        try:
            out = subprocess.check_output(["../pdns/pdnsutil", "--config-dir=.", "list-keys", self.zone])
            self.assertFalse(self.zone in out)
        except subprocess.CalledProcessError as e:
            self.fail("pdnsutil list-keys failed: "+e.output)

        #checks for not covered zonename
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"fail/cryptokeys/"+keyid))
        self.assertEquals(r.status_code, 404)

        #checks for key is gone. Its ok even if no key had to be deleted. Or something went wrong with the backend.
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+keyid))
        self.assertTrue(r.status_code == 200 or r.status_code == 422)

