import ciphers

from ctypes import *

class cipher(ciphers.cipherTemplate):

	def __init__(self):

		self._name = 'RussianTEA'
		self._plaintextLength = 8
		self._keyLength = 16
		self._ciphertextLength = 8

	def encipher(self, inputText, key):
		
		assert len(inputText) == 2*self._plaintextLength, "Bad parameter size for enciphering " + self._name

		encInputText = self._encode(inputText)
		encKey = self._encode(key)

		y=c_uint32(encInputText[0])
		z=c_uint32(encInputText[1])

		sum=c_uint32(0)
		delta=0x9E3779B9
		n=32
		w=[0,0]

		while(n>0):
			sum.value += delta
			y.value += ( z.value << 4 ) + (encKey[0] ^ z.value) + (sum.value ^ ( z.value >> 5 )) + encKey[1]
			z.value += ( y.value << 4 ) + (encKey[2] ^ y.value) + (sum.value ^ ( y.value >> 5 )) + encKey[3]
			n -= 1

		w[0]=y.value
		w[1]=z.value

		return self._decode(w) 

	def decipher(self, inputText, key):

		assert len(inputText) == 2*self._ciphertextLength, "Bad parameter size for deciphering " + self._name
		
		encInputText = self._encode(inputText)
		encKey = self._encode(key)

		y=c_uint32(encInputText[0])
		z=c_uint32(encInputText[1])

		sum=c_uint32(0xC6EF3720)
		delta=0x9E3779B9
		n=32
		w=[0,0]

		while(n>0):
			z.value -= ( y.value << 4 ) + (encKey[2] ^ y.value) + (sum.value ^ ( y.value >> 5 )) + encKey[3]
			y.value -= ( z.value << 4 ) + (encKey[0] ^ z.value) + (sum.value ^ ( z.value >> 5 )) + encKey[1]
			sum.value -= delta
			n -= 1

		w[0]=y.value
		w[1]=z.value

		return self._decode(w)

	def _encode(self, inputText):
		
		k = [0] * (len(inputText)/8)
		for i in range(0,len(inputText)/8):
			k[i] = int(inputText[8*i:8*(i+1)],16)

		return k

	def _decode(self, inputText):
		
		return hex((inputText[0] << 32) + inputText[1])[2:-1]

	def getName(self):

		return self._name

	def getPlaintextLength(self):

		return self._plaintextLength

	def getKeyLength(self):

		return self._keyLength

	def getCiphertextLength(self):

		return self._ciphertextLength