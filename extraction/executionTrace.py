#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# Aligot project

# Simple framework to write algorithms on execution traces. The trace is
# collected by a tracer (usually Pin) and a "connector" feeds an
# executionTrace object.

# Copyright, licence: who cares?
# ----------------------------------------------

import os
import mmap

# Aligot modules

import utilities

class executionTrace:

    ''' 
        An execution trace is a list of dynamic instructions.
    '''

    def __init__(self):
        self.instructions = list()

    def display(self, m, r):
        print '--------- TRACE ---------'
        for ins in self.instructions:
            ins.display(m, r)

    def string(self):
        p = []
        for ins in self.instructions:
            p.append(ins.string())
        return p


class instruction:

    '''
        This class represents a *dynamic* instruction, that
        is an address, a machine instruction and its effects on the system
    '''

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
        self.constants = []  # Like 0x0 in mov eax, 0x0

        # Integers

        self.memoryReadSize = []
        self.memoryWriteSize = []

    def __str__(self):
        return self.x86ASM

    def __eq__(self, e):
        return e.x86ASM == self.x86ASM

    def __ne__(self, e):
        return not self.__eq__(e)

    def firstOperand(self):
        operands = str(self).split(',')
        if operands[0].find(' ') != -1: # push eax
            return (operands[0])[operands[0].find(' ') + 1:]
        else:
            return None

    def secondOperand(self):
        operands = str(self).split(',')
        if len(operands) == 2:
            return (operands[1])[1:]
        else:
            return None

    def isALoop(self):
        return self.x86ASM.startswith('+L')

    def display(self, m=0, r=0):

        '''
            m and r indicate the level of display for memory and registers respectively:
               - 0 don't display
               - 1 for read accesses only
               - 2 for write accesses only
               - 3 for both
        '''

        print '0x' + self.address + ' ' + self.x86ASM,

        if len(self.apiCall) != 0:
            print ' ' + self.apiCall,

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

        print ''

######################
# Trace parsing
######################

def lineConnector(line):
    
    '''
        Take a line from an execution trace following our format, and builds
        the corresponding instruction object.

        The current trace format looks like this:

        1000b8e4!push 0x70!RR_esp_12ffc4!WM_12ffc0_4_70!WR_esp_12ffc0   
        1000b8e6!push 0x100162f2!RR_esp_12ffc0!WM_12ffbc_4_100162f2!WR_esp_12ffbc
        1000b8eb!call 0x10011e24!RR_esp_12ffbc!WM_12ffb8_4_1000b8f0!WR_esp_12ffb8
    '''

    if line.startswith('API CALL'):
        return None
    else:
        myLine = line.split('!')

        if len(myLine) > 1:
            ins = instruction(myLine[0], myLine[1].strip())

            # Constants

            if ins.secondOperand() is not None and ins.secondOperand().startswith('0x'):
                if len(ins.secondOperand()[2:]) == 8:

                    # 4-bytes
                    ins.constants.append(ins.secondOperand()[2:])

            for info in myLine:

                if info.startswith('RR'):
                    readRegisters = info.split('_')
                    for i in range(1, len(readRegisters), 2):
                        ins.registersRead.append(readRegisters[i])
                        ins.registersReadValue.append(utilities.normalizeValueToRegister(readRegisters[i+ 1].strip(), 
                                                                                            readRegisters[i]))

                if info.startswith('WR'):
                    writeRegisters = info.split('_')
                    for i in range(1, len(writeRegisters), 2):
                        ins.registersWrite.append(writeRegisters[i])
                        ins.registersWriteValue.append(utilities.normalizeValueToRegister(writeRegisters[i+ 1].strip(), 
                                                                                            writeRegisters[i]))

                if info.startswith('WM'):
                    writeMemory = info.split('_')
                    for i in range(1, len(writeMemory), 4):
                        ins.memoryWriteAddress.append(writeMemory[i])
                        ins.memoryWriteSize.append(int(writeMemory[i+ 1], 16))
                        norVal = utilities.normalizeValueToSize(writeMemory[i+ 2].strip(), 
                                                            int(writeMemory[i + 1],
                                                            16))
                        ins.memoryWriteValue.append(norVal)

                if info.startswith('RM'):
                    readMemory = info.split('_')
                    for i in range(1, len(readMemory), 4):
                        ins.memoryReadAddress.append(readMemory[i])
                        ins.memoryReadSize.append(int(readMemory[i+ 1], 16))
                        norVal = utilities.normalizeValueToSize(readMemory[i + 2].strip(), 
                                                                int(readMemory[i + 1],
                                                                16))
                        ins.memoryReadValue.append(norVal)

            return ins
        else:
            if line != '\n':
                print 'Error in readling line (connector)'
                print line
            return None
