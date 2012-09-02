#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# Aligot project

# Various functions.

# Copyright, licence: who cares?
# ----------------------------------------------

# General Purpose Registers

GPR32 = set(['eax','ebx','ecx','edx','esi','edi','esp','ebp'])

GPR16 = set(['ax','bx','cx','dx','si','di','sp','bp'])

def registersAddress(reg):

    if reg in GPR32:
        return [reg + '0', reg + '1', reg + '2', reg + '3']

    if reg in GPR16:
        return ['e' + reg + '2', 'e' + reg + '3']

    # AH,AL,BH...
    if reg[1] == 'h':
        return ['e' + reg[0] + 'x2']

    elif reg[1] == 'l':
        return ['e' + reg[0] + 'x3']
    
    print 'Error during registers parsing, register length: ' + len(reg)
    quit()


def normalizeValueToSize(val, size):
    ''' Returns val as an hexa string of length 2 * size '''
    
    return val.zfill(2*size)


def getRegisterLength(reg):

    if reg in GPR32:
        return 4
    elif reg in GPR16:
        return 2
    else:
        return 1


def normalizeValueToRegister(val, reg):
    ''' Returns val as an hexa string of length 2 * register length '''

    return val.zfill(2*getRegisterLength(reg))

    
def bigToLittleEndian(leVal):
    '''Take a 8 hex char input value in little endian order and transform it
        in big endian order...'''

    beVal = ''
    for i in range(0, len(leVal), 2):
        beVal = leVal[i:i + 2] + beVal

    return beVal


def isAscii(input):

    # return (((i>=0x30) and (i<=0x39)) or ((i>=0x41) and (i<=0x54)) or ((i>=0x61)and(i<=0x7a)))

    return input >= 0x20 and input <= 0x7E


def main():

    print registersAddress('eax')
    print registersAddress('esp')
    print registersAddress('sp')
    print registersAddress('bp')
    print registersAddress('cx')
    print registersAddress('cl')
    print registersAddress('ch')
    print registersAddress('esi')
    print registersAddress('si')


if __name__ == '__main__':
    main()
