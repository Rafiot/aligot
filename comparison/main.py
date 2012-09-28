#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# Aligot project
#
# Identification module
#
# Copyright, licence: who cares?
# ----------------------------------------------

# TODO (random order):
#
# - Really integrate AES (PyCrypto), MD5 (PyCrypto), Modular Multiplication
#   (Montgomery), currently we use tweaked external module to check for these
#   algorithms. 
# - The tool is currently only usable with a cipher argument, we should 
#   add a "default" mode where all ciphers are tested 
# - Think of a better way to allow the user to add its own algorithms 
#   (think custom algorithms, not in python) .
# - When a specific algorithm is designated by the user, only
# generate I/O values with the corresponding length 
# - Possible improvement: remove doublons for values 
# - Add decoding procedures for endiannes, big number libraries... 
# - Add "heuristics": 
#        + memory adjacency, i.e. prefer values containing original adjacent parameters 
#        + removal of fixed value inputs, e.g. AES SBOX, TEA delta,...


__doc__ = \
    """
Aligot project. This module takes care of the actual identification of possible crypto algorithms.
It takes as input the result file produced by the extraction module.
"""

__version__ = '1'
__versionTime__ = '09/12'
__author__ = 'j04n'

import os
import itertools
import binascii
import argparse
from datetime import datetime

## Reference implementations

# PyCrypto

from Crypto.Cipher import ARC4

# Custom

import referenceImplementations.xtea as xtea
import referenceImplementations.tea as tea
import referenceImplementations.russian_tea as russian_tea
import referenceImplementations.tea_parametrized as tea_parametrized


ldfgList = list()  # list of extractedLdfg objects


class extractedLdfg:

    def __init__(self):

        # I/O values from the extracted result file

        self.inputValues = dict()  # index -> value
        self.outputValues = dict()

        # Filled by the combination step

        self.possibleInputParameterValues = dict()  # length (bytes) -> value
        self.possibleOutputParameterValues = dict()


def main():

    parser = \
        argparse.ArgumentParser(description='Identification of crypto algorithms based on their input-output values.'
                                )
    parser.add_argument('--xtea', dest='xtea', action='store_true',
                        default=False)
    parser.add_argument('--xtea-x', dest='xtea_x', action='store_true',
                        default=False)
    parser.add_argument('--tea', dest='tea', action='store_true',
                        default=False)
    parser.add_argument('--tea-x', dest='tea_x', action='store_true',
                        default=False)
    parser.add_argument('--tea-russian', dest='tea_russian',
                        action='store_true', default=False)
    parser.add_argument('--rc4', dest='rc4', action='store_true',
                        default=False)
    parser.add_argument('--xor', dest='xor', action='store_true',
                        default=False)
    parser.add_argument('-dg', dest='debug_mode', action='store_true',
                        default=False)
    parser.add_argument('resultsFile', action='store')
    args = parser.parse_args()

    connectWithresultsFile(args.resultsFile)

    print ''
    print '> Aligot identification module'

    print '> Start:',
    print datetime.now()
    print '---------------------------\n'

    for ldfg in ldfgList:
        buildPossibleInputParameters(ldfg, args)
        buildPossibleOutputParameters(ldfg, args)

    comparison(args)

    print '\n---------------------------'
    print '> End:',
    print datetime.now()


def connectWithresultsFile(fileName):

    ''' Given the result file produced by the Aligot extraction module, builds
        a list of extractedLdfg objects. '''

    f = open(fileName, 'r')

    # Jump over the header

    line = f.readline()
    line = f.readline()
    line = f.readline()

    # Here is the real stuff

    for line in f:

        newLdfg = extractedLdfg()

        inputs = line.split(':')[0]
        outputs = line.split(':')[1]

        if len(inputs.split(',')) >= 10:
            print "\nERROR: More than 10 input parameters - You should try to narrow them (eg. remove memory addresses)"
            quit() # Pretty rough, we could still allow the execution ?
        if len(outputs.split(',')) >= 10:
            print "\nERROR: More than 10 output parameters - You should try to narrow them (eg. remove memory addresses)"
            quit()

        if len(inputs) and len(outputs):

            for iv in inputs.split(','):

                # We need the integer value, not a string

                value = iv.decode('hex')
                newLdfg.inputValues[len(newLdfg.inputValues.keys())] = \
                    value

            for ov in outputs.split(','):

                # We need the integer value, not a string

                value = ov.strip().decode('hex')
                newLdfg.outputValues[len(newLdfg.outputValues.keys())] = \
                    value

            ldfgList.append(newLdfg)

    f.close()


def buildPossibleInputParameters(ldfg, args):

    ''' Build each possible parameter (that is each possible length) as a list
        of indexes, each of these index corresponding to a value in the result
        file. The list represents the concatenation of such values. 
        (Done this way in order to use itertools module)'''

    # We need a string as '12...n' where n is the number of input values
    # (to use itertools module)

    myValues = ''
    for k in range(0, len(ldfg.inputValues.keys())):
        myValues += str(k)

    inputParameterValues = list(itertools.permutations(myValues, 1))

    # For each possible length
    for i in range(2, len(ldfg.inputValues.keys())+1):

        if args.debug_mode:
            print 'Round ' + str(i)

        inputParameterValues.extend(list(itertools.permutations(myValues,
                                    i)))

    for p in inputParameterValues:
        length = 0

        for i in p:
            length += len(ldfg.inputValues[int(i)])

        if length in ldfg.possibleInputParameterValues.keys():
            ldfg.possibleInputParameterValues[length].append(p)
        else:
            ldfg.possibleInputParameterValues[length] = list([p])


def buildPossibleOutputParameters(ldfg, args):

    ''' Build each possible parameter (that is each possible length) as a list
        of indexes, each of these index corresponding to a value in the result
        file. The list represents the concatenation of such values. 
        (Done this way in order to use itertools module)'''

    # We need a string as '12...n' where n is the number of output values
    # (to use itertools module)

    myValues = ''
    for k in range(0, len(ldfg.outputValues.keys())):
        myValues += str(k)

    outputParameterValues = list(itertools.permutations(myValues, 1))

    # For each possible length
    for i in range(2, len(ldfg.outputValues.keys())+1):
        if args.debug_mode:
            print 'Round ' + str(i)
        outputParameterValues.extend(list(itertools.permutations(myValues,
                i)))

    for p in outputParameterValues:
        length = 0

        for i in p:
            length += len(ldfg.outputValues[int(i)])

        if length in ldfg.possibleOutputParameterValues.keys():
            ldfg.possibleOutputParameterValues[length].append(p)
        else:
            ldfg.possibleOutputParameterValues[length] = list([p])


def buildInputValue(indiceList, currentLdfg):

    ''' Given an indexes list, and an LDFG, returns the associated input value
        (integer). '''

    value = ''
    for i in indiceList:
        value += currentLdfg.inputValues[int(i)].encode('hex')

    return value.decode('hex')


def buildOutputValue(indiceList, currentLdfg):

    ''' Given an indexes list, and an LDFG, returns the associated output
        value (integer). '''

    value = ''
    for i in indiceList:
        value += currentLdfg.outputValues[int(i)].encode('hex')

    return value.decode('hex')


def comparison(args):

    global ldfgList

    # For each unknown LDFG

    for currentLdfg in ldfgList:

        print '> Comparison phase starting...',
        print str(len(currentLdfg.inputValues.keys())) + ' inputs - ',
        print str(len(currentLdfg.outputValues.keys())) + ' outputs'

        

        # ------------------
        # # Category 1
        # ------------------
        # Block ciphers with 16-bytes key, 8-bytes input text, 8-bytes output text
        # TEA, XTEA, Russian TEA

        if args.xtea or args.tea or args.tea_russian:

            cipher = '(16,8:8)'

            if args.xtea:
                cipher = 'XTEA ' + cipher
            if args.tea:
                cipher = 'TEA ' + cipher
            if args.tea_russian:
                cipher = 'Russian TEA ' + cipher

            print '\n> Test for ' + cipher + ' encryption/decryption...',
            suitableParameters = 1
            possibleOutputs = set()

            try:

                # These are indexes list

                possibleKey = \
                    currentLdfg.possibleInputParameterValues[16]
                possibleInputText = \
                    currentLdfg.possibleInputParameterValues[8]
                possibleOutputText = \
                    currentLdfg.possibleOutputParameterValues[8]

                # Build a set with output parameter *values* for O(1) test
                # (possible because the ciphers have only one output parameter)

                for outputTextIndice in possibleOutputText:
                    possibleOutputs.add(binascii.hexlify(buildOutputValue(outputTextIndice,
                            currentLdfg)))
            except:

                suitableParameters = 0
                print '> Fail: no suitable parameters found'

            if suitableParameters == 1:

                found = 0

                # We test all input possibilities

                for keyIndice in possibleKey:
                    for inputTextIndice in possibleInputText:

                        if found == 1:

                            # We stop as soon we found a match

                            return

                        key = buildInputValue(keyIndice, currentLdfg)
                        inputText = buildInputValue(inputTextIndice,
                                currentLdfg)

                        # Calls to reference implementations

                        if args.xtea:

                            referenceOutputD = xtea.xtea_decrypt(key,
                                    inputText).encode('hex')

                            referenceOutputE = xtea.xtea_encrypt(key,
                                    inputText).encode('hex')

                        if args.tea:

                            # Specific encoding for TEA reference implementation

                            k = [int(key.encode('hex')[0:8], 16),
                                 int(key.encode('hex')[8:16], 16),
                                 int(key.encode('hex')[16:24], 16),
                                 int(key.encode('hex')[24:32], 16)]
                            v = [int(inputText.encode('hex')[0:8], 16),
                                 int(inputText.encode('hex')[8:16], 16)]

                            r = tea.decipher(v, k)

                            referenceOutputD = hex((r[0] << 32)
                                    + r[1])[2:-1]  # probably a better way to do that...

                            r = tea.encipher(v, k)

                            referenceOutputE = hex((r[0] << 32)
                                    + r[1])[2:-1]  # probably a better way to do that...

                        if args.tea_russian:

                             # Specific encoding for Russian TEA reference implementation

                            k = [int(key.encode('hex')[0:8], 16),
                                 int(key.encode('hex')[8:16], 16),
                                 int(key.encode('hex')[16:24], 16),
                                 int(key.encode('hex')[24:32], 16)]
                            v = [int(inputText.encode('hex')[0:8], 16),
                                 int(inputText.encode('hex')[8:16], 16)]

                            r = russian_tea.decipher(v, k)

                            referenceOutputD = hex((r[0] << 32)
                                    + r[1])[2:-1]  # probably a better way to do that...

                            r = russian_tea.encipher(v, k)

                            referenceOutputE = hex((r[0] << 32)
                                    + r[1])[2:-1]  # probably a better way to do that...

                        # Do we have the reference output in our generated output values ?

                        if referenceOutputD in possibleOutputs:

                            print '''!! Found ''' + cipher + ' decryption !!'

                            print ' ==> Key (16 bytes) : ' \
                                + binascii.hexlify(key)
                            print '\n ==> Crypted text (8 bytes) : ' \
                                + binascii.hexlify(inputText)[0:16]
                            print '\n ==> Decrypted text (8 bytes) : ' \
                                + referenceOutputD

                            found = 1

                        if referenceOutputE in possibleOutputs:

                            print '''!! Found ''' + cipher + ' encryption !!'

                            print ' ==> Key (16 bytes)' \
                                + binascii.hexlify(key)
                            print '\n ==> Deypted text (8 bytes) : ' \
                                + binascii.hexlify(inputText)[0:16]
                            print '\n ==> Encrypted text (8 bytes) : ' \
                                + referenceOutputE

                            found = 1

        # ------------------
        # # Category 2
        # ------------------
        # Block ciphers with 16-bytes key, 8-bytes input text, 4-bytes delta, 4-bytes round number, 8-bytes output text
        # TEA and XTEA parametrized

        if args.tea_x or args.xtea_x:

            cipher = '(16,8,4,4:8)'

            if args.tea_x:
                cipher = 'TEA Modified ' + cipher
            if args.xtea_x:
                cipher = 'XTEA Modified ' + cipher

            print '\n> Test for ' + cipher + ' encryption/decryption...',

            suitableParameters = 1
            possibleOutputs = set()

            try:

                # These are indexes list

                possibleKey = \
                    currentLdfg.possibleInputParameterValues[16]
                possibleInputText = \
                    currentLdfg.possibleInputParameterValues[8]
                possibleDelta = \
                    currentLdfg.possibleInputParameterValues[4]
                possibleRoundNumber = \
                    currentLdfg.possibleInputParameterValues[4]
                possibleOutputText = \
                    currentLdfg.possibleOutputParameterValues[8]

                # Build a set with output parameters to ease the check
                # Only possible because all ciphers have one output parameter

                for outputTextIndice in possibleOutputText:
                    possibleOutputs.add(binascii.hexlify(buildOutputValue(outputTextIndice,
                            currentLdfg)))
            except:
                print ' fail: no suitable parameters found'
                suitableParameters = 0

            if suitableParameters:
                found = 0

                for keyIndice in possibleKey:
                    for inputTextIndice in possibleInputText:
                        for deltaIndice in possibleDelta:
                            for roundNumberIndice in \
                                possibleRoundNumber:

                                if found == 1:

                                    # We stop as soon we found a match

                                    return

                                key = buildInputValue(keyIndice,currentLdfg)

                                inputText = buildInputValue(inputTextIndice, currentLdfg)

                                myDelta = buildInputValue(deltaIndice, currentLdfg)

                                myRoundNumber = buildInputValue(roundNumberIndice, currentLdfg)

                                if args.tea_x:

                                    # Specific encoding for TEA reference implementation

                                    k = [int(key.encode('hex')[0:8],16), 
                                        int(key.encode('hex')[8:16], 16), 
                                        int(key.encode('hex')[16:24], 16), 
                                        int(key.encode('hex')[24:32], 16)]
                                    v = [int(inputText.encode('hex')[0:8], 16), 
                                        int(inputText.encode('hex')[8:16], 16)]

                                    # Delta needs to be an int

                                    d = int(myDelta.encode('hex'), 16)
                                    rn = int(myRoundNumber.encode('hex'), 16)

                                    if rn < 1 or rn > 0x100:
                                        continue  # Improbable round number (document this shit somewhere)

                                    r = tea_parametrized.decipher(v, k, d, rn)

                                    referenceOutputD = hex((r[0] << 32) + r[1])[2:-1] 

                                    r = tea_parametrized.encipher(v, k, d, rn)

                                    referenceOutputE = hex((r[0] << 32) + r[1])[2:-1]  # probably a better way to do that...

                                # Comparison

                                if referenceOutputD in possibleOutputs:

                                    print '''\n\n!! Found ''' + cipher + ' decryption !!'

                                    print ' ==> Key (16 bytes) : 0x' + binascii.hexlify(key)
                                    print '\n ==> Delta (4 bytes) : 0x' + binascii.hexlify(myDelta)
                                    print '\n ==> Round number (4 bytes) : 0x' + binascii.hexlify(myRoundNumber)
                                    print '\n ==> Crypted text (8 bytes) : 0x' + binascii.hexlify(inputText)[0:16]
                                    print '\n ==> Decrypted text (8 bytes) : ' + referenceOutputD
                                    found = 1

                                if referenceOutputE in possibleOutputs:

                                    print '''!! Found ''' + cipher + ' encryption !!'

                                    print ' ==> Key (16 bytes) : 0x' + binascii.hexlify(key)
                                    print '\n ==> Delta (4 bytes) : 0x' + binascii.hexlify(myDelta)
                                    print '\n ==> Round number (4 bytes) : 0x' + binascii.hexlify(myRoundNumber)
                                    print '\n ==> Decrypted text (8 bytes) : 0x' + binascii.hexlify(inputText)[0:16]
                                    print '\n ==> Encrypted text (8 bytes) : ' + referenceOutputE
                                    found = 1

        # ------------------
        # # Category 3
        # ------------------
        # Variable length input text, variable length key, variable length output text (stream ciphers)
        # RC4

        if args.rc4:

            cipher = '(VL,VL:VL)'

            if args.rc4:
                cipher = 'RC4 ' + cipher

            print '\n> Test for ' + cipher + ' encryption/decryption...',

            # Store all possible input texts and keys, i.e. all possible length inputs
            # These are indexes list

            possibleKey = list()
            possibleInputText = list()
            
            for length in currentLdfg.possibleInputParameterValues.keys():

                possibleKey.extend(currentLdfg.possibleInputParameterValues[length])
                possibleInputText.extend(currentLdfg.possibleInputParameterValues[length])

            # Build a set with output parameter *values* for O(1) test

            possibleOutputs = set() # for O(1) tests

            for length in currentLdfg.possibleOutputParameterValues.keys():

                for outputTextIndice in currentLdfg.possibleOutputParameterValues[length]:

                    possibleOutputs.add(binascii.hexlify(buildOutputValue(outputTextIndice,
                                currentLdfg)))

            #print possibleOutputs

            found = 0

            for keyIndice in possibleKey:
                for inputTextIndice in possibleInputText:

                    if found == 1:

                        # We stop as soon we found a match

                        return

                    # Endianess assumed to be BIG ENDIAN 

                    keyBE = buildInputValue(keyIndice, currentLdfg)
                    inputTextBE = buildInputValue(inputTextIndice,
                            currentLdfg)

                    rc4Cipher = ARC4.new(keyBE)
                    resultRC4 = binascii.hexlify(rc4Cipher.decrypt(inputTextBE))

                    # Comparison with the possible output values of the same length

                    if resultRC4 in possibleOutputs:

                        print '''\n\n ** Found ''' + cipher + " encryption/decryption "

                        print ' ==> Key (' + str(len(keyBE)) + ' bytes) : '+ binascii.hexlify(keyBE)

                        print '\n ==> Crypted text (' + str(len(inputTextBE)) + ' bytes) : ',

                        if len(inputTextBE) >= 32:
                            print binascii.hexlify(inputTextBE)[0:16] + '...'
                        else:
                            print binascii.hexlify(inputTextBE)

                        print '\n ==> Decrypted text (' + str(len(resultRC4.decode('hex'))) + ' bytes) : ',
                        
                        if len(resultRC4.decode('hex')) >= 32:
                            print binascii.hexlify(resultRC4.decode('hex'))[0:16] + '...'
                        else:
                            print binascii.hexlify(resultRC4.decode('hex'))
                        
                        found = 1
                        break

if __name__ == '__main__':
    main()
