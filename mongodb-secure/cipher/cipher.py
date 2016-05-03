class Cipher:

	def __init__(self,keys=None):
		self.keys = keys
		return

	def encrypt(self,x):
		return x

	def decrypt(self,c):
		return c

	@staticmethod
	def keygen(key_size):
		return None

	def has_keys(self):
		return True if self.keys and self.keys.has_key("pub") and self.keys.has_key("priv") else False

	def get_public_key(self):
		if self.keys is None:
			raise Exception("There is no keys!")
		if not self.keys.has_key("pub"):
			raise Exception("There is no public key!")
		
		return self.keys["pub"]

	def get_private_key(self):
		if self.keys is None:
			raise Exception("There is no keys!")		
		if not self.keys.has_key("priv"):
			raise Exception("There is no private key!")

		return self.keys["priv"]

	def add_to_public_key(self,name,value):
		if self.keys is None:
			self.keys = {}
		if not self.keys.has_key("pub"):
			self.keys["pub"] = {}

		self.keys["pub"][name] = value

	def add_to_private_key(self,name,value):
		if self.keys is None:
			self.keys = {}
		if not self.keys.has_key("priv"):
			self.keys["priv"] = {}

		self.keys["priv"][name] = value