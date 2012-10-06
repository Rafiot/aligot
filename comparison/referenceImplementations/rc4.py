#!/usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------
# Aligot project
#
# Copyright, licence: who cares?
# ----------------------------------------------

import ciphers

from Crypto.Cipher import ARC4

class cipher(ciphers.cipherTemplate):

	def __init__(self):

		self._name = 'RC4'
		self._plaintextLength = -1
		self._keyLength = -1
		self._ciphertextLength = -1

	def encipher(self, inputText, key):
		
		from Crypto.Cipher import ARC4

		encKey = self._encode(key)
		encInputText = self._encode(inputText)
		
		cipher = ARC4.new(encKey)
		outputText = cipher.encrypt(encInputText)

		return self._decode(outputText)


	def decipher(self, inputText, key):
		
		'''
			Same as encipher
		'''

		return self.encipher(inputText,key)

	def _encode(self, inputText):

		return inputText.decode('hex')

	def _decode(self, inputText):

		return inputText.encode('hex')

	def getBlacklistedValues(self):

		return {}

	def getName(self):

		return self._name

	def getPlaintextLength(self):

		return self._plaintextLength

	def getKeyLength(self):

		return self._keyLength

	def getCiphertextLength(self):

		return self._ciphertextLength