class parameter():

    def __init__(self, startAddress, length, value):

        self.startAddress = startAddress # string, either hexa value or 'R'|'C' for registers|constants
        self.length = length # int, in bytes
        self.value = value # hexa string

    def incrementSize(self,value):

        self.length +=1
        self.value += value

    def display(self):

        print self.startAddress + '|' + hex(self.length)[2:] + '|' + self.value