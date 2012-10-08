#!/usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------
# Aligot project
#
# Comparison module
#
# Copyright, licence: who cares?
# ----------------------------------------------

__doc__ = \
    """
Aligot project. This module takes care of the actual identification of possible crypto algorithms.
It takes as input the result file produced by the extraction module.
"""

# TODO: 
#
# - Allows more than 2-input parameters functions:
#       + hash functions
#       + parametrized implementations (tea)
# - Allows different input/output lengths
# - One thread for each cipher ?
# - Integrate decoding procedures for endiannes, big number libraries... 
# - Test that ciphers implement all the needed methods

__version__ = '1'
__versionTime__ = '10/12'
__author__ = 'j04n'

import argparse
from datetime import datetime
from collections import defaultdict
import itertools

import referenceImplementations.ciphers as ciphers
import heuristics
import parameter


class LDF():

    def __init__(self):

        self.inputParameters = dict()  # id -> parameter
        self.outputParameters = dict()
        self.minLengthInput = 0x10000 # for combinations generation
        self.minLengthOutput = 0x10000
        self.maxLengthInput = 0x0
        self.maxLengthOutput = 0x0

    def display(self):

        print '> inputs:'
        for ip in self.inputParameters.values():
            ip.display()
        print '> outputs:'
        for op in self.outputParameters.values():    
            op.display()

def main():

    parser = argparse.ArgumentParser(description='Identification of crypto \
                                                algorithms based on their input-output values.')
    
    parser.add_argument('resultsFile', action='store')

    parser.add_argument('--debug',
                            help='debug display',
                            action='store_true')

    parser.add_argument('--ciphers',
                            nargs='*',
                            choices=ciphers.implementedCiphers)
    
    parser.add_argument('--no-mem-heuristic-input', # by default we apply it
                        dest='no_mem_heuristic_input',
                        action='store_true')

    parser.add_argument('--no-mem-heuristic-output', # by default we apply it
                        dest='no_mem_heuristic_output',
                        action='store_true')
    
    parser.add_argument('--no-bl-heuristic', # by default we apply it
                        dest='no_bl_heuristic',
                        action='store_true')

    parser.add_argument('--bl-input-registers', # by default we *dont* apply it
                        help='Registers are not considered as input parameters',
                        dest='bl_input_registers',
                        action='store_true')

    parser.add_argument('--bl-output-registers', # by default we *dont* apply it
                        help='Registers are not considered as output parameters',
                        dest='bl_output_registers',
                        action='store_true')
    
    args = parser.parse_args()

    print ''
    print '> Aligot identification module'

    print '> Start:',
    print datetime.now()
    print '-----------------------------------'

    dbLDF = connectResultFile(args.resultsFile)


    if args.ciphers is None:
        print "> No particular ciphers selected, test with all of them :",
        print ciphers.implementedCiphers
        listOfCiphers = instantiateCiphers(ciphers.implementedCiphers)
    else:
        listOfCiphers = instantiateCiphers(args.ciphers)

    count = 1
    for ldf in dbLDF:
        
        print "\n> Testing LDF " + str(count) + " ..."
        
        if (len(ldf.inputParameters.keys()) > 10) and not args.no_mem_heuristic_input:
            print '  > Heuristic : Memory adjacency, more than 10 input parameters (disable it with --no-mem-heuristic-input)'
            heuristics.inputMemoryAdjacency(ldf)

        if (len(ldf.outputParameters.keys()) > 10) and not args.no_mem_heuristic_output:
            print '  > Heuristic : Memory adjacency, more than 10 output parameters (disable it with --no-mem-heuristic-output)'
            heuristics.outputMemoryAdjacency(ldf)

        if args.bl_input_registers:
            print '  > Heuristic : Remove input registers from parameters'
            heuristics.filterInputRegisters(ldf)

        if args.bl_output_registers:
            print '  > Heuristic : Remove output registers from parameters'
            heuristics.filterOutputRegisters(ldf)

        for c in listOfCiphers:
            
            if not args.no_bl_heuristic:
                print '  > Heuristic : Blacklisting classic values for ' + c.getName() + ' (disable it with --no-bl-heuristic)'
            
                bl = heuristics.blacklistedValues(ldf, c)

                if args.debug and (len(bl[0]) != 0):
                    print '    > Blacklisted input values : '
                    for blp in bl[0]:
                        print '\t\t' + str(blp)
                
                if args.debug and len(bl[1]) != 0:
                    print '    > Blacklisted output values : '
                    for blp in bl[1]:
                        print '\t\t' + str(blp)


            if args.debug:
                print '  > Tested LDF:'
                ldf.display()

            # Here is the magic
            if compare(ldf,c):
                break

        count+=1

    print '\n-----------------------------------'
    print '> End:',
    print datetime.now()

def compare(ldf, refCipher):

    print "  > Comparison with " + refCipher.getName() + "...",

    [i1,i2,o] = generateParameterOrganization(ldf, 
                                                refCipher.getPlaintextLength(),
                                                refCipher.getKeyLength(),
                                                refCipher.getCiphertextLength())
    
    possibleInput1s = buildInputValues(ldf,i1)
    possibleInput2s = buildInputValues(ldf,i2)
    possibleOutputs = buildOutputValues(ldf,o)

    hashFunctionFound = 0

    for i1 in possibleInput1s:

        if (refCipher.getPlaintextLength() != -1) and (len(i1)/2 != refCipher.getPlaintextLength()):
            continue

        for i2 in possibleInput2s:

            if (refCipher.getKeyLength() != -1) and (len(i2)/2 != refCipher.getKeyLength()):
                continue

            if refCipher.encipher(i1,i2) in possibleOutputs:

                ciphertext = refCipher.encipher(i1,i2)

                print "\n\n!! Identification successful: " + refCipher.getName() + " encryption with:" 
                print ' ==> Plain text (' + str(len(i1)/2) + ' bytes) : 0x' + i1
                if not refCipher.hashFunction:
                    print ' ==> Key ('+ str(len(i2)/2) +' bytes) : 0x' + i2
                if not refCipher.hashFunction:
                    print ' ==> Encrypted text (' + str(len(ciphertext)/2) + ' bytes) : 0x' + ciphertext
                    return True
                else:
                    print ' ==> Hash (' + str(len(ciphertext)/2) + ' bytes) : 0x' + ciphertext
                    hashFunctionFound = 1
            
            if not refCipher.hashFunction:
                if refCipher.decipher(i1,i2) in possibleOutputs:

                    plaintext = refCipher.decipher(i1,i2)

                    print "\n\n!! Identification successful: " + refCipher.getName() + " decryption with:"
                    print ' ==> Encrypted text (' + str(len(i1)/2) + ' bytes) : 0x' + i1
                    print ' ==> Key ('+ str(len(i2)/2) +' bytes) : 0x' + i2
                    print ' ==> Decrypted text (' + str(len(plaintext)/2) + ' bytes) : 0x' + plaintext
                    return True

    if hashFunctionFound:
        return True
    else:
        print "Fail!"
        return False

def buildOutputValues(ldf,organizations):

    r = set()

    for o in organizations:
        val = ''
        for index in o:
            val += ldf.outputParameters[index].value
        r.add(val)

    return r

def buildInputValues(ldf,organizations):

    r = set()

    for o in organizations:
        val = ''
        for index in o:
            val += ldf.inputParameters[index].value
        r.add(val)

    return r

def generateParameterOrganization(ldf, input1Length = -1, input2Length = -1, outputLength = -1):

    '''
        Given a particular LDF, and parameter filters, generate the corresponding combinations of parameters. 
        Such combination is defined as a list of parameter index for ldf.
        Returns a tuple [a,b,c] where a,b,c are respectively input 1, input 2 and output possible organizations.
    '''
    
    # ** Inputs

    # Generate a reference string with parameter IDs appended
    referenceList = [i for i in range(len(ldf.inputParameters.keys()))]

    if len(referenceList) > 10:

            print '\n\nWARNING: The number of input values to combined is pretty high (' + str(len(referenceList)) + ')'
            print '\t  You should check for specific ciphers, or at least try to remove some non-crypto values (memory addresses, counter...)'

    # * Input 1

    if input1Length != -1:

        # Calculate lower and upper bounds of the number of parameters to combined
        # in order to respect parameter filter

        combinationMaxLengthI1 = input1Length // ldf.minLengthInput
        combinationMinLengthI1 = input1Length // ldf.maxLengthInput # Could be better


        possibleCombinationsI1 = list()

        # For each possible length
        for i in range(combinationMinLengthI1, combinationMaxLengthI1+1):
            possibleCombinationsI1.extend(list(itertools.permutations(referenceList,i)))

    else:

        possibleCombinationsI1 = generateAllCombinations(referenceList)

    # * Input 2

    if input2Length != -1:

        combinationMaxLengthI2 = input2Length // ldf.minLengthInput
        combinationMinLengthI2 = input2Length // ldf.maxLengthInput

        possibleCombinationsI2 = list()

        for i in range(combinationMinLengthI2, combinationMaxLengthI2+1):
            possibleCombinationsI2.extend(list(itertools.permutations(referenceList,i)))
    else:

        possibleCombinationsI2 = generateAllCombinations(referenceList)

    # ** Output

    referenceList = [i for i in range(len(ldf.outputParameters.keys()))]

    if len(referenceList) > 10:

            print '\n\nWARNING: The number of output values to combined is pretty high (' + str(len(referenceList)) + ')'
            print '\t  You should check for specific ciphers, or at least try to remove some non-crypto values (memory addresses, counter...)'

    if outputLength != -1:

        combinationMaxLengthO = outputLength // ldf.minLengthOutput
        combinationMinLengthO = outputLength // ldf.maxLengthOutput

        possibleCombinationsO = list()

        for i in range(combinationMinLengthO, combinationMaxLengthO+1):
            possibleCombinationsO.extend(list(itertools.permutations(referenceList,i)))

    else:
        
        possibleCombinationsO = generateAllCombinations(referenceList)

    return [possibleCombinationsI1,possibleCombinationsI2,possibleCombinationsO]

def generateAllCombinations(l):

    possibleCombinations = list()

    # For each possible length
    i = 1
    while len(list(itertools.permutations(l,i))) != 0:
        possibleCombinations.extend(list(itertools.permutations(l,i)))
        i += 1

    return possibleCombinations

def instantiateCiphers(cipherList):

    listOfCiphers = []

    for newCipher in cipherList:

        # Is there a better way to do that ?
        exec('import referenceImplementations.%s' % newCipher)
        exec('c=referenceImplementations.%s.cipher()' % newCipher)

        listOfCiphers.append(c)

    return listOfCiphers

def connectResultFile(filename):

    ''' Given the result file produced by the Aligot extraction module, builds
        a list of LDFs. '''

    f = open(filename, 'r')

    # Jump over the header

    f.readline()
    f.readline()
    f.readline()

    dbLDF = list()

    for line in f:
        inputs = line.split(":")[0]
        outputs = line.split(":")[1].rstrip()

        curLDF = LDF()

        for inputParam in inputs.split(','):

            inputAddr = inputParam.split('|')[0]
            inputVal = inputParam.split('|')[1]

            byteLength = len(inputVal)/2
            if byteLength < curLDF.minLengthInput:
                curLDF.minLengthInput = byteLength

            if byteLength > curLDF.maxLengthInput:
                curLDF.maxLengthInput = byteLength

            p = parameter.parameter(inputAddr,byteLength, inputVal)  

            newId = len(curLDF.inputParameters.keys())          
            curLDF.inputParameters[newId] = p

        for outputParam in outputs.split(','):

            outputAddr = outputParam.split('|')[0]
            outputVal = outputParam.split('|')[1]
 
            byteLength = len(outputVal)/2 
            if byteLength < curLDF.minLengthOutput:
                curLDF.minLengthOutput = byteLength

            if byteLength > curLDF.maxLengthOutput:
                curLDF.maxLengthOutput = byteLength

            p = parameter.parameter(outputAddr,byteLength,outputVal)

            newId = len(curLDF.outputParameters.keys())
            curLDF.outputParameters[newId] = p

        dbLDF.append(curLDF)

    f.close()

    return dbLDF

if __name__=="__main__":
    main()