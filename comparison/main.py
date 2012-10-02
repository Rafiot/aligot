# TODO: test that ciphers implement all the needed methods

__doc__ = \
    """
Aligot project. This module takes care of the actual identification of possible crypto algorithms.
It takes as input the result file produced by the extraction module.
"""

# TODO: 
# - integrates hash functions (0 length parameter)

__version__ = '1'
__versionTime__ = '10/12'
__author__ = 'j04n'

import argparse
from datetime import datetime
from collections import defaultdict
import itertools

import referenceImplementations.ciphers as ciphers


class LDF():

    def __init__(self):

        self.inputValues = dict()  # id -> parameter
        self.outputValues = dict()
        self.minLengthInput = 0x10000 # for combinations generation
        self.minLengthOutput = 0x10000
        self.maxLengthInput = 0x0
        self.maxLengthOutput = 0x0

    def display(self):

        print self.inputValues
        print self.outputValues

class parameter():

    def __init__(self, length, value):

        self.length = length # int, in bytes
        self.value = value # hexa string


def main():

    parser = argparse.ArgumentParser(description='Identification of crypto \
                                                algorithms based on their input-output values.')
    parser.add_argument('resultsFile', action='store')
    parser.add_argument('--ciphers',
                            nargs='*',
                            choices=ciphers.implementedCiphers)
    args = parser.parse_args()

    print ''
    print '> Aligot identification module'

    print '> Start:',
    print datetime.now()
    print '-----------------------------------\n'

    dbLDF = connectResultFile(args.resultsFile)

    if args.ciphers is None:
        print "> No particular ciphers selected, test with all of them :",
        print ciphers.implementedCiphers
        listOfCiphers = instantiateCiphers(ciphers.implementedCiphers)
    else:
        listOfCiphers = instantiateCiphers(args.ciphers)

    count = 1
    for ldf in dbLDF:
        
        print "> Testing LDF " + str(count) + " ..."

        for c in listOfCiphers:
            if compare(ldf,c):
                break

        count+=1

    print '\n-----------------------------------'
    print '> End:',
    print datetime.now()

def compare(ldf, refCipher):

    print "  > Comparison with " + refCipher._name + "...",

    [i1,i2,o] = generateParameterOrganization(ldf, 
                                                refCipher.getPlaintextLength(),
                                                refCipher.getKeyLength(),
                                                refCipher.getCiphertextLength())
    
    possibleInput1s = buildInputValues(ldf,i1)
    possibleInput2s = buildInputValues(ldf,i2)
    possibleOutputs = buildOutputValues(ldf,o)

    for i1 in possibleInput1s:


        if (refCipher.getPlaintextLength() != -1) and (len(i1)/2 != refCipher.getPlaintextLength()):
            continue

        for i2 in possibleInput2s:

            if (refCipher.getKeyLength() != -1) and (len(i2)/2 != refCipher.getKeyLength()):
                continue

            if refCipher.encipher(i1,i2) in possibleOutputs:

                print "\n\n!! Identification successful: " + refCipher._name + " encryption with:"
                print "> " + refCipher._name + " encryption"
                print ' ==> Plain text (' + str(refCipher.getPlaintextLength()) + ' bytes) : 0x' + i1
                print ' ==> Key ('+ str(refCipher.getKeyLength()) +' bytes) : 0x' + i2
                print ' ==> Encrypted text (' + str(refCipher.getCiphertextLength()) + ' bytes) : 0x' + refCipher.encipher(i1,i2)
                return True
            
            elif refCipher.decipher(i1,i2) in possibleOutputs:

                print "\n\n!! Identification successful: " + refCipher._name + " decryption with:"
                print ' ==> Encrypted text (' + str(refCipher.getCiphertextLength()) + ' bytes) : 0x' + i1
                print ' ==> Key ('+ str(refCipher.getKeyLength()) +' bytes) : 0x' + i2
                print ' ==> Decrypted text (' + str(refCipher.getPlaintextLength()) + ' bytes) : 0x' + refCipher.decipher(i1,i2)
                return True


    print "Fail!"
    return False

def buildOutputValues(ldf,organizations):

    r = set()

    for o in organizations:
        val = ''
        for index in o:
            val += ldf.outputValues[index].value
        r.add(val)

    return r

def buildInputValues(ldf,organizations):

    r = set()

    for o in organizations:
        val = ''
        for index in o:
            val += ldf.inputValues[index].value
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
    referenceList = [i for i in range(len(ldf.inputValues.keys()))]

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

    referenceList = [i for i in range(len(ldf.outputValues.keys()))]

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

        for inputVal in inputs.split(","):
            
            byteLength = len(inputVal)/2
            if byteLength < curLDF.minLengthInput:
                curLDF.minLengthInput = byteLength

            if byteLength > curLDF.maxLengthInput:
                curLDF.maxLengthInput = byteLength

            p = parameter(byteLength, inputVal)  
            newId = len(curLDF.inputValues.keys())          
            curLDF.inputValues[newId] = p

        for outputVal in outputs.split(","):
 
            byteLength = len(outputVal)/2 
            if byteLength < curLDF.minLengthOutput:
                curLDF.minLengthOutput = byteLength

            if byteLength > curLDF.maxLengthOutput:
                curLDF.maxLengthOutput = byteLength

            p = parameter(byteLength,outputVal)
            newId = len(curLDF.outputValues.keys())
            curLDF.outputValues[newId] = p

        dbLDF.append(curLDF)

    f.close()

    return dbLDF

if __name__=="__main__":
    main()