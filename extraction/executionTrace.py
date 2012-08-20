#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# Aligot project
# This module contains a simple framework to write algorithms on execution traces

# The trace is collected by a tracer (Pin) and a "connector" feeds
# our representation here

# Copyright, licence: who cares?
# ----------------------------------------------

import os
import utilities
import mmap

debugMode = 0

# address (int) and registers (string!)

inputBytes = dict()
outputBytes = dict()  # @ -> value (last one)

class executionTrace:

    ''' An execution trace is a list of dynamic instructions.'''

    def __init__(self):
        self.instructions = list()

    def display(self, m, r):
        print '--------- TRACE ---------'
        for ins in self.instructions:
            ins.display(m, r)

    def projectionOnInst(self):
        p = []
        for ins in self.instructions:
            p.append(ins.projectionOnInst())
        return p


class instruction:

    '''This class represents a *dynamic* instruction, that
        is an address, a machine instruction and its effects on the system'''

    # Storing the machine instruction with an assembly representation is
    # probably not a good idea, due the syntactic differences among assemblers
    # Still, that's what we do :(

    def __init__(self, addr, insASM):

        # Strings

        self.address = addr
        self.memoryReadAddress = []
        self.memoryWriteAddress = []
        self.registersRead = []
        self.registersWrite = []
        self.memoryReadValue = []
        self.memoryWriteValue = []
        self.registersReadValue = []
        self.registersWriteValue = []
        self.x86ASM = insASM
        self.apiCall = ''
        self.constants = []  # Like in mov eax, 0x0

        # Integers

        self.memoryReadSize = []
        self.memoryWriteSize = []

    def equal(self, e):
        return e.x86ASM == self.x86ASM

    def string(self):
        return self.x86ASM

    def projectionOnInst(self):
        return self.x86ASM

    def firstOperand(self):
        operands = self.projectionOnInst().split(',')
        if operands[0].find(' ') != -1:
            return (operands[0])[operands[0].find(' ') + 1:]
        else:
            return None

    def secondOperand(self):
        operands = self.projectionOnInst().split(',')
        if len(operands) == 2:
            return (operands[1])[1:]
        else:
            return None

    def isALoop(self):
        return self.x86ASM[0] == '+' and self.x86ASM[1] == 'L'

    def display(self, m=0, r=0):

        # Classic display

        print '0x' + self.address + ' ' + self.x86ASM,

        if len(self.apiCall) != 0:
            print ' ' + self.apiCall,

        # Registers
        # 0 don't display
        # 1 for read
        # 2 for write
        # 3 for both

        if r == 1 or r == 3:
            if self.registersRead != []:
                print '\n\t[RR',
                for i in range(0, len(self.registersRead)):
                    print ' ' + self.registersRead[i] + ':' \
                        + self.registersReadValue[i],
                print ']',
        if r == 2 or r == 3:
            if self.registersWrite != []:
                print '\n\t[WR',
                for i in range(0, len(self.registersWrite)):
                    print ' ' + self.registersWrite[i] + ':' \
                        + self.registersWriteValue[i],
                print ']',

        # Memory
        # 0 don't display
        # 1 for read
        # 2 for write
        # 3 for both

        if m == 1 or m == 3:
            if self.memoryReadAddress != []:
                print '\n\t[RM',
                for i in range(0, len(self.memoryReadAddress)):
                    print ' ' + self.memoryReadAddress[i] + ':' \
                        + str(self.memoryReadSize[i]) + ':' \
                        + self.memoryReadValue[i],
                print ']',
        if m == 2 or m == 3:
            if self.memoryWriteAddress != []:
                print '\n\t[WM',
                for i in range(0, len(self.memoryWriteAddress)):
                    print ' ' + self.memoryWriteAddress[i] + ':' \
                        + str(self.memoryWriteSize[i]) + ':' \
                        + self.memoryWriteValue[i],
                print ']',

        print '\n',


def fileConnector(myTraceFileName,myTrace,limit=0,startAddr='',endAddr=''):
    '''Take an execution trace and build the corresponding object. 

        Not a good idea for big files (cf. lineConnector()). 

        The current trace format is something like this:

        1000b8e4!push 0x70!RR_esp_12ffc4!WM_12ffc0_4_70!WR_esp_12ffc0   
        1000b8e6!push 0x100162f2!RR_esp_12ffc0!WM_12ffbc_4_100162f2!WR_esp_12ffbc
        1000b8eb!call 0x10011e24!RR_esp_12ffbc!WM_12ffb8_4_1000b8f0!WR_esp_12ffb8'''

    f = open(myTraceFileName, 'r+')
    map = mmap.mmap(f.fileno(), 0)

    countLine = 0

    if startAddr == 0:
        start = 1
    else:
        start = 0  # Wait for start address
        if debugMode:
            print 'Waits for ' + startAddr + ' ' + endAddr

    line = map.readline()
    while line != '':

        countLine += 1

        myLine = line.split('!')
        if not start:
            if len(myLine) > 1:
                if startAddr == myLine[0]:
                    if debugMode:
                        print 'Start!'
                    start = 1
        else:
            if endAddr == myLine[0]:
                if debugMode:
                    print 'End !'
                break

            # Api call

            if line.find('API CALL') == 0:
                apiLine = line.split(' ')
                myTrace.instructions[-1].apiCall = (apiLine[2])[:-1]
            else:

            # Classic instruction

                myLine = line.split('!')

                if len(myLine) > 1:
                    ins = instruction(myLine[0], myLine[1].strip())

                    for info in myLine:

                        if info.find('RR') != -1:
                            readRegisters = info.split('_')
                            for i in range(1, len(readRegisters), 2):
                                ins.registersRead.append(readRegisters[i])
                                ins.registersReadValue.append(utilities.normalizeValueToRegister(readRegisters[i
                                        + 1].strip(), readRegisters[i]))

                        if info.find('WR') != -1:
                            writeRegisters = info.split('_')
                            for i in range(1, len(writeRegisters), 2):
                                ins.registersWrite.append(writeRegisters[i])
                                ins.registersWriteValue.append(utilities.normalizeValueToRegister(writeRegisters[i
                                        + 1].strip(),
                                        writeRegisters[i]))

                        if info.find('WM') != -1:
                            writeMemory = info.split('_')
                            for i in range(1, len(writeMemory), 4):
                                ins.memoryWriteAddress.append(writeMemory[i])
                                ins.memoryWriteSize.append(int(writeMemory[i
                                        + 1], 16))
                                norVal = \
                                    utilities.normalizeValueToSize(writeMemory[i
                                        + 2].strip(), int(writeMemory[i
                                        + 1], 16))
                                norVal = \
                                    utilities.bigToLittleEndian(norVal)
                                ins.memoryWriteValue.append(norVal)

                        if info.find('RM') != -1:
                            readMemory = info.split('_')
                            for i in range(1, len(readMemory), 4):
                                ins.memoryReadAddress.append(readMemory[i])
                                ins.memoryReadSize.append(int(readMemory[i
                                        + 1], 16))
                                norVal = \
                                    utilities.normalizeValueToSize(readMemory[i
                                        + 2].strip(), int(readMemory[i
                                        + 1], 16))
                                norVal = \
                                    utilities.bigToLittleEndian(norVal)
                                ins.memoryReadValue.append(norVal)

                    myTrace.instructions.append(ins)

                if countLine % 100000 == 0:
                    print 'Connection with 100000 lines...'

                if countLine == limit:
                    print "We've reached the limit " + str(limit) \
                        + ' : end of connection...'
                    f.close()
                    return

        line = map.readline()

    # To avoid nasty problems when the trace ends with a loop, we add a useless instruction

    eot = instruction('0', 'EOT')
    myTrace.instructions.append(eot)

    f.close()


def lineConnector(line):
    '''Take a line from an execution trace following our format, and builds
        the corresponding instruction object'''

    if line.find('API CALL') == 0:
        return -1
    else:
        myLine = line.split('!')

        if len(myLine) > 1:
            ins = instruction(myLine[0], myLine[1].strip())

            # Constants

            if ins.secondOperand() != None and ins.secondOperand()[:2] \
                == '0x':
                if len(ins.secondOperand()[2:]) == 8:

                    # 4-bytes

                    ins.constants.append(ins.secondOperand()[2:])

            for info in myLine:

                if info.find('RR') != -1:
                    readRegisters = info.split('_')
                    for i in range(1, len(readRegisters), 2):
                        ins.registersRead.append(readRegisters[i])
                        ins.registersReadValue.append(utilities.normalizeValueToRegister(readRegisters[i
                                + 1].strip(), readRegisters[i]))

                if info.find('WR') != -1:
                    writeRegisters = info.split('_')
                    for i in range(1, len(writeRegisters), 2):
                        ins.registersWrite.append(writeRegisters[i])
                        ins.registersWriteValue.append(utilities.normalizeValueToRegister(writeRegisters[i
                                + 1].strip(), writeRegisters[i]))

                if info.find('WM') != -1:
                    writeMemory = info.split('_')
                    for i in range(1, len(writeMemory), 4):
                        ins.memoryWriteAddress.append(writeMemory[i])
                        ins.memoryWriteSize.append(int(writeMemory[i
                                + 1], 16))
                        norVal = \
                            utilities.normalizeValueToSize(writeMemory[i
                                + 2].strip(), int(writeMemory[i + 1],
                                16))

                        # norVal = utilities.bigToLittleEndian(norVal)

                        ins.memoryWriteValue.append(norVal)

                if info.find('RM') != -1:
                    readMemory = info.split('_')
                    for i in range(1, len(readMemory), 4):
                        ins.memoryReadAddress.append(readMemory[i])
                        ins.memoryReadSize.append(int(readMemory[i
                                + 1], 16))
                        norVal = \
                            utilities.normalizeValueToSize(readMemory[i
                                + 2].strip(), int(readMemory[i + 1],
                                16))

                        # Endianness problem (should be managed by the comparison part):
                        # norVal = utilities.bigToLittleEndian(norVal)

                        ins.memoryReadValue.append(norVal)

            return ins
        else:
            if line != '\n':
                print 'Error in readling line (connector)'
                print line
            return -1
