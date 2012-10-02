
implementedCiphers = ['tea','rc4','xtea']


class cipherTemplate():

	'''
		Template to define a reference cipher. Each method has to be implemented.
	'''

	def encipher(self, inputText, key):
		
		'''
			Input are passed as hexadecimal strings.
		'''

		raise NotImplementedError("Missing encipher method")

	def decipher(self, inputText, key):
		
		'''
			Input are produced as hexadecimal strings.
		'''

		raise NotImplementedError("Missing decipher medthod")

	def _encode(self, inputText):
		
		'''
			Translate hexadecimal strings in the implementation format.
		'''

		raise NotImplementedError("Missing encoding method")

	def _decode(self, inputText):
		
		'''
			Translate implementation format in to hexadecimal strings.
		'''

		raise NotImplementedError("Missing decoding method")

	def getName(self):

		raise NotImplementedError("Missing getName method")

	def getInputTextLength(self):

		raise NotImplementedError("Missing getInputTextLength method")

	def getKeyLength(self):

		raise NotImplementedError("Missing getKeyLength method")

	def getOutputTextLength(self):

		raise NotImplementedError("Missing getOutputTextLength method")



