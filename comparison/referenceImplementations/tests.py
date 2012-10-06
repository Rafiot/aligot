#!/usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------
# Aligot project
#
# Copyright, licence: who cares?
# ----------------------------------------------

import rc4
import tea
import xtea

def main():

	# Test RC4
	key = '53757065724b657949734153757065724b6579'
	inputT = '5375706572506c61696e4d6573736167654142617365446554726f6d7065747465'
	outputT = 'd3e852f160d60dd627d66860e97148f57a71ada22f319ac8bdcf7053e071bce29e'

	c = rc4.cipher()
	assert(c.decipher(inputT,key) == outputT)

	# Test TEA
	key = 'deadbee1deadbee2deadbee3deadbee4'
	inputT = '0123456789abcdef'
	outputT = 'df5ec1536e089494'

	c = tea.cipher()
	assert(c.decipher(inputT,key) == outputT)

	# Test XTEA
	key = 'deadbee1deadbee2deadbee3deadbee4'
	inputT = '0123456789abcdef'
	outputT = '56700fa3624cd258'

	c = xtea.cipher()
	assert(c.decipher(inputT,key) == outputT)

if __name__ == '__main__':
    main()