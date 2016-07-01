import subprocess
import json
import sys

from test_helper import ApiTestCase

class Cryptokeys(ApiTestCase):
    zone = "cryptokeyzone.com."
    def setUp(self):
        super(Cryptokeys, self).setUp()
        payload = {
            'name': self.zone,
            'kind': 'Native',
            'nameservers': ['ns1.example.com.', 'ns2.example.com.']
        }
        # Create zone for testing
        r = self.session.post(
            self.url("/api/v1/servers/localhost/zones"),
            data=json.dumps(payload),
            headers={'content-type': 'application/json'})
        self.assert_success_json(r)

    def tearDown(self):
        super(Cryptokeys,self).tearDown()
        # Removes zone
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/" + self.zone))
        self.assertEquals(r.status_code, 204)
        self.assertNotIn('Content-Type', r.headers)

    # Retuns all public data from all keys from self.zone
    def get_keys(self):
        r = self.session.get(
            self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys"))
        self.assert_success_json(r)
        return r.json()

    # Prepares the json object for Post and sends it to the server
    def add_key(self, content='', type='ksk', active='true' , algo='', bits=0, assertion=True):
        if algo == '':
            payload = {
                'keytype': type,
                'active' : active
            }
        else:
            payload = {
                'keytype': type,
                'active' : active,
                'algo' : algo
            }
        if bits > 0:
            payload['bits'] = bits
        if content != '':
            payload['content'] = content
        r = self.session.post(
            self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys"),
            data=json.dumps(payload),
            headers={'content-type': 'application/json'})
        if assertion:
            self.assert_success_json(r)
            self.assertEquals(r.status_code, 201)
        return r

    # This methode test the DELETE api call. Sometimes 200 or 422 are valid return codes,
    # because it "could" happen that the backend crashes during the test or the remove function returns false.
    # In this case 422 is correct. I don't know how to force false backend behavior. So i assume that the backend
    # works correct.
    def test_delete(self):
        r = self.add_key(type='ksk')

        keyid = str(r.json()['id'])

        #checks the status code. I don't know how to test explicit that the backend fail removing a key.
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+keyid))
        self.assertTrue(r.status_code == 200 or r.status_code == 422)

        # Check that the key is actually deleted
        keys = [k['id'] for k in self.get_keys()]
        self.assertFalse(keyid in keys)

        #checks for not covered zonename
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"fail/cryptokeys/"+keyid))
        self.assertEquals(r.status_code, 400)

        #checks for key is gone. Its ok even if no key had to be deleted. Or something went wrong with the backend.
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+keyid))
        self.assertTrue(r.status_code == 200 or r.status_code == 422)

    # Removes a key by id using the pdnsutil command
    def remove_key(self, keyid):
        #checks for key is gone. Its ok even if no key had to be deleted. Or something went wrong with the backend.
        r = self.session.delete(self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+str(keyid)))
        self.assertTrue(r.status_code == 200)

    # Tests POST for a positiv result and deletes the added key
    def post_helper(self,content='', algo='', bits=0):
        r = self.add_key(content=content, algo=algo, bits=bits)

        response = r.json()

        # Only a ksk added, so expected type is csk
        self.assertEquals(response['keytype'], 'csk')
        keyid = response['id']

        # Check if the key is actually added
        keys = [k['id'] for k in self.get_keys()]
        self.assertTrue(keyid in keys)

        # Remove it for further testing
        self.remove_key(keyid)

    def test_post(self):
        # Test add a key with default algorithm
        self.post_helper()

        # Test add a key with specific number
        self.post_helper(algo=10, bits=512)

        # Test add a key with specific name and bits
        self.post_helper(algo="rsasha256", bits=256)

        # Test add a key with specific name
        self.post_helper(algo='ecdsa256')

        # Test add a private key from extern resource
        self.post_helper(content="Private-key-format: v1.2\n"+
                            "Algorithm: 8 (RSASHA256)\n"+
                            "Modulus: 4GlYLGgDI7ohnP8SmEW8EBERbNRusDcg0VQda/EPVHU=\n"+
                            "PublicExponent: AQAB\n"+
                            "PrivateExponent: JBnuXF5zOtkjtSz3odV+Fk5UNUTTeCsiI16dkcM7TVU=\n"+
                            "Prime1: /w7TM4118RoSEvP8+dgnCw==\n"+
                            "Prime2: 4T2KhkYLa3w7rdK3Cb2ifw==\n"+
                            "Exponent1: 3aeKj9Ct4JuhfWsgPBhGxQ==\n"+
                            "Exponent2: tfh1OMPQKBdnU6iATjNR2w==\n"+
                            "Coefficient: eVrHe/kauqOewSKndIImrg==)\n")

        # Test wrong key format
        r = self.add_key(content="trollololoooolll",assertion=False)
        self.assert_error_json(r)
        self.assertEquals(r.status_code, 422)
        self.assertIn("Wrong key format!",r.json()['error'])

        # Test wrong keytype
        r = self.add_key(type='sdfdhhgj',assertion=False)
        self.assert_error_json(r)
        self.assertEquals(r.status_code, 422)
        self.assertIn("Invalid keytype",r.json()['error'])

        #Test unsupported algorithem
        r = self.add_key(algo='lkjhgf',assertion=False)
        self.assert_error_json(r)
        self.assertEquals(r.status_code, 422)
        self.assertIn("Unknown algorithm:",r.json()['error'])

        #Test add a key and forgot bits
        r = self.add_key(algo="rsasha256",assertion=False)
        self.assert_error_json(r)
        self.assertEquals(r.status_code, 422)
        self.assertIn("key requires the size (in bits) to be passed", r.json()['error'])

        #Test wrong bit size
        r = self.add_key(algo=10, bits=30,assertion=False)
        self.assert_error_json(r)
        self.assertEquals(r.status_code,422)
        self.assertIn("Wrong bit size!", r.json()['error'])

        #Test can't guess key size
        r = self.add_key(algo=15,assertion=False)
        self.assert_error_json(r)
        self.assertEquals(r.status_code,422)
        self.assertIn("Can't guess key size for algorithm", r.json()['error'])

    def is_key_active(self, key_id):
        # check if key is activated
        for k in self.get_keys():
            if k['id'] == key_id:
                return k['active']

    def test_put_activate_deactivate_key(self):
        #create key
        r = self.add_key()
        keyid = r.json()['id']

        # activate key
        payload = {
            'active': True
        }
        o = self.session.put(
            self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+str(keyid)),
            data=json.dumps(payload),
            headers={'content-type': 'application/json'})
        self.assertEquals(o.status_code, 200)

        # check if key is activated
        self.assertTrue(self.is_key_active(keyid))

        # deactivate key
        payload2 = {
            'active': False
        }
        q = self.session.put(
            self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+str(keyid)),
            data=json.dumps(payload2),
            headers={'content-type': 'application/json'})
        self.assertEquals(q.status_code, 200)
        self.assert_success_json(q)

        # check if key is deactivated
        self.assertFalse(self.is_key_active(keyid))

        # Remove it for further testing
        self.remove_key(keyid)

    def test_put_deactivate_deactivated_activate_activated_key(self):
        #create key
        r = self.add_key()
        keyid = r.json()['id']

        # deactivate key
        payload = {
            'active': False
        }
        q = self.session.put(
            self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+str(keyid)),
            data=json.dumps(payload),
            headers={'content-type': 'application/json'})
        self.assertEquals(q.status_code, 200)
        self.assert_success_json(q)

        # check if key is still deactivated
        self.assertFalse(self.is_key_active(keyid))

        # activate key
        payload2 = {
            'active': True
        }
        o = self.session.put(
            self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+str(keyid)),
            data=json.dumps(payload2),
            headers={'content-type': 'application/json'})
        self.assertEquals(o.status_code, 200)

        # check if key is activated
        self.assertTrue(self.is_key_active(keyid))

        #activate again
        z = self.session.put(
            self.url("/api/v1/servers/localhost/zones/"+self.zone+"/cryptokeys/"+str(keyid)),
            data=json.dumps(payload2),
            headers={'content-type': 'application/json'})
        self.assertEquals(z.status_code, 200)

        # check if key is still activated
        self.assertTrue(self.is_key_active(keyid))