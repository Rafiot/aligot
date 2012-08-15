#!/usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------
# Aligot project

# Here is implemented the "variable" notion (parameters are variables with
# fixed values..)

# Copyright, licence: who cares?
# ----------------------------------------------


class variable:

    def display(self, mode=0):

        if self.registerName != '':
            print self.registerName + ':' + str(self.size) + ' ',
        else:
            print hex(self.startAddress) + ':' + str(self.size) + ' ',

        if mode == 1:
            for k in self.value.keys():
                print self.value[k],

    def equal(self, var):
        return (self.startAddress == var.startAddress) & (self.size
                == var.size)

    def incrementSize(self):

        self.value[self.size] = '00'
        self.size += 1

    def intersects(self, otherVar):

        # Applies only to memory variables

        if self.registerName != '' or otherVar.registerName != '':
            return 0
        else:
            return (otherVar.startAddress >= self.startAddress) \
                & (otherVar.startAddress < self.startAddress
                   + self.size) | (self.startAddress
                                   >= otherVar.startAddress) \
                & (self.startAddress < otherVar.startAddress
                   + otherVar.size)

    def merge(self, otherVar):
        endAddress = max(self.startAddress + self.size,
                         otherVar.startAddress + otherVar.size)
        startAddress = min(self.startAddress, otherVar.startAddress)

        var = variable(startAddress, endAddress - startAddress)
        return var

    def contains(self, otherVar):

        # Our var contains otherVar if:
        # - otherVar startaddress is equal or more our sa
        # - otherVar endaddress is no more than our end address

        # applies only to memory variables

        if self.registerName != '' or otherVar.registerName != '':
            return 0
        else:
            return (otherVar.startAddress >= self.startAddress) \
                & (otherVar.startAddress + otherVar.size
                   <= self.startAddress + self.size)

    # Either startAddress is null and registerName not null, or the contrary

    def __init__(
        self,
        startAddress,
        size,
        registerName='',
        ):

        # ints!

        self.startAddress = startAddress
        self.registerName = registerName
        self.size = size
        self.loopInstanceID = 0
        self.pydotNodeID = 0
        self.constant = 0  # Indicates if the variable is constant (u fucking nub)

        self.value = dict()
        for i in range(0, self.size):
            self.value[i] = '00'
