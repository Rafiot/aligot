#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# Aligot project

# Deal with loop detection and the building of their I/O parameters. A loop is
# defined a the repetition of a same sequence of machine instructions in an
# execution trace.

# Copyright, licence: who cares?
# ----------------------------------------------

import copy
import pydot

# Aligot modules

import utilities
import executionTrace
import variable

debugMode = 0x0


class loop:

    ''' 
        A loop is identified by its body, that is a list of machine
        instructions or loop IDs (representing nested loops). Each 
        execution of a loop corresponds to a different instance 
        (cf. loopInstance())
    '''

    def __init__(self,id,startTime,l,):

        self.ID = id
        self.body = l  # List of machine instructions or loop IDs (stored as "+L" ID)

        self.instances = dict() # Instance IDs -> loopInstance()
        self.instances[0x0] = loopInstance(0x0, startTime, 1 % len(self.body), 1)
        self.numberOfInstances = 1

    

    def display(self, mode=0x0):

        ''' 
            Display mode = 0 for valid instances only, 1 for all instances.
        '''

        if mode == 0x0:
            validInstance = 0x0
            for i in self.instances.keys():
                if self.instances[i].valid == 1:
                    if validInstance == 0x0:
                        print '\n************** Loop %d **************' \
                            % self.ID
                        validInstance = 1
                    self.instances[i].display(0x0)
            if validInstance:
                print 'Body : '
                for ins in self.body:
                    ins.display()
                print '\n************************************'
        elif mode == 1:

            print '\n************** Loop %d **************' % self.ID
            for i in self.instances.keys():
                self.instances[i].display(1)
            print 'Body : '
            for ins in self.body:
                ins.display()
            print '\n************************************'

    def __eq__(self, loopToCompare):

        if len(loopToCompare.body) != len(self.body):
            return 0x0
        else:

            # Compare each instruction with its "vis-a-vis"

            cursor = 0x0
            for ins in loopToCompare.body:
                if ins != self.body[cursor]:
                    return 0x0
                cursor += 1
            return 1

    def __ne__(self, loopToCompare):

        return not self.__eq__(loopToCompare)

    def addInstance(self,startTime,cursor,turn,startAddress='',):

        self.instances[self.numberOfInstances] = \
            loopInstance(self.numberOfInstances, startTime, cursor,
                         turn, startAddress)

        self.numberOfInstances += 1

        # Returns the instance ID

        return self.numberOfInstances - 1


class loopInstance:

    '''
        A same loop can have several instances with different startAddress
    '''

    def __init__(self,id,startTime,cursor,turn,startAddr='',):

        self.ID = id
        self.waitFor = cursor  # Index on the loop body for the next awaited instruction
        self.close = 0x0 # to 1 if the loop instance is finished
        self.valid = 0x0 # to 1 if the loop instance iterated at least two times
        self.turns = turn # number of iterations
        self.startTime = startTime
        self.endTime = 0x0 # default
        self.startAddress = startAddr

        self.imbricatedInstanceID = list()  # List of nested loop instances contained in this one 
                                            # [[loopID,InstanceID]...],

        self.inputMemoryParameters = list() # filled by buildLoopIOMemory()
        self.outputMemoryParameters = list()

        self.inputRegisterParameters = list() # filled by buildLoopIORegisters()
        self.outputRegisterParameters = list()

        self.constantParameter = list() # filled by buildLoopIOConstants()

        self.pydotNodeID = 0x0  # Mandatory for graph display with pydot

    def display(self, mode=0x0):

        print '=> Instance %d' % self.ID
        print ' SA = 0x%s  w8for = %d - close = %d - valid = %d - turns = %d - startTime = %d - endTime = %d ' \
            % (
            self.startAddress,
            self.waitFor,
            self.close,
            self.valid,
            self.turns,
            self.startTime,
            self.endTime,
            )

        print '\ninput memory parameters ' + str(len(self.inputMemoryParameters))
        for v in self.inputMemoryParameters:
            v.display(mode)

        print '\ninput register parameters ' + str(len(self.inputRegisterParameters))
        for v in self.inputRegisterParameters:
            v.display(mode)

        print '\noutput memory parameters ' + str(len(self.outputMemoryParameters))
        for v in self.outputMemoryParameters:
            v.display(mode)

        print '\noutput register parameters ' + str(len(self.outputRegisterParameters))
        for v in self.outputRegisterParameters:
            v.display(mode)
        print ""




def garbageCollector(loopStorage):

    ''' 
        Remove loops whose all instances are invalid. 
    '''

    for loopKey in loopStorage.keys():
        hasValidInstance = False

        for instKey in loopStorage[loopKey].instances.keys():
            if loopStorage[loopKey].instances[instKey].valid == 1:
                hasValidInstance = True
            else:
                loopStorage[loopKey].instances.pop(instKey)

        if not hasValidInstance:
            loopStorage.pop(loopKey)


def garbageCollectorUselessLoops(loopStorage):
    
    ''' 
        Remove loops whose all instances don't have any I/O parameters. 
    '''

    for loopKey in loopStorage.keys():
        hasValidIOInstance = False

        for instKey in loopStorage[loopKey].instances.keys():
            if len(loopStorage[loopKey].instances[instKey].inputMemoryParameters) != 0x0 \
                or len(loopStorage[loopKey].instances[instKey].outputMemoryParameters) != 0x0 \
                or len(loopStorage[loopKey].instances[instKey].inputRegisterParameters) != 0x0 \
                or len(loopStorage[loopKey].instances[instKey].outputRegisterParameters) != 0x0:
                hasValidIOInstance = True
            else:
                loopStorage[loopKey].instances.pop(instKey)

        if not hasValidIOInstance:
            loopStorage.pop(loopKey)

def displayLoopStorage(loopStorage, mode=0x0):

    # mode : 0 : default (only valid loops)
    #        1 : all loops

    print '\nLoopStorage:'
    for k in loopStorage.keys():
        loopStorage[k].display(mode)

############################
# LOOP DETECTION
############################

# Good to know :
#  - when there is a nested loop that is matched we wait for the
#   child loop, and there is one turn on the history at this point, so during
#   the validation the classic double body suppression fail
#  - we consider API calls to be the same for all loop instances

onGoingLoopsStacks = list()  # The order is important, it represents the loop age

class executionHistory:

    ''' 
        A list of [timestamp, (machine instruction||loop ID)] used for loop detection. 
    '''

    def __init__(self):

        self.elements = list()

    def append(self, ins, time):
        self.elements.append([time, ins])

    def pop(self):
        return self.elements.pop()

    def reverse(self):
        rHistory = executionHistory()
        rHistory.elements = self.elements
        rHistory.elements.reverse()
        return rHistory

    # Return a list of lists of [timestamp, (machine instruction||loop ID)] that could be a loop body

    def possibleLoops(self, instToLookFor):
        
        myCopyHistory = list()
        listOfBodies = list()

        # Backward pass

        for i in range(len(self.elements)-1, -1, -1):

            element = self.elements[i]
            myCopyHistory.insert(0,element)

            # When we find the instruction, we get the body of the associated possible loop

            if element[1] == instToLookFor:
                newCopy = copy.copy(myCopyHistory)
                listOfBodies.append(newCopy)

        return listOfBodies

    # Take a list of instructions to suppress, starting at the end of the history

    def suppressByTheEnd(self, body):

        if body == []:
            if debugMode:
                print '++ The list of instructions to suppress is empty!'
            return

        rBody = copy.copy(body)
        rBody.reverse()
        for inst in rBody:
            if self.elements[-1][1] == inst:
                self.pop()
            else:
                if debugMode:
                    print '++ Fail to suppress this instruction (Can be normal for nested loops):'
                    print '\t' + str(inst)


    def display(self):
        for e in self.elements:
            print '[ t:' + str(e[0x0]) + ' ins: ' + str(e[1]) + ']'
   

class stackOfLoop:

    ''' 
        A stack containing loop instances, where the stack order represents
        the loop nesting. The stack head is the most nested loop. Each loop
        instance is stored as a string "LoopID-InstanceID"     
    '''

    def __init__(self):
        self.elements = list()

    def push(self, e):
        self.elements.append(e)

    def pop(self):
        return self.elements.pop()

    def head(self):
        return self.elements[-1]

    def reverse(self):
        rStack = stackOfLoop()
        rStack.elements = self.elements
        rStack.elements.reverse()
        return rStack

    def display(self):
        for e in self.elements:
            print '[' + e + ']'

    def empty(self):
        return len(self.elements) == 0x0


def detectLoop(myTraceFileName):     
    
    ''' 
        Recognition of a loop (a word in the language w.w) from the machine
        instructions in an execution trace. 
    '''

    global onGoingLoopsStacks

    loopStorage = dict()
    history = executionHistory()

    f = open(myTraceFileName, 'r')

    time = 0x0
    for line in f:

        if time != 0x0 and time % 100000 == 0x0:
            print '100000 lines...'

        if debugMode == 1:
            if time != 0x0 and time % 10000 == 0x0:
                print 'S:10000 lines...'
                print 'History depth'
                print len(history.elements)

            if time != 0x0 and time % 1000 == 0x0:
                print 'SS:1000 lines...'
                print 'History depth'
                print len(history.elements)

                # history.display()

        ins = executionTrace.lineConnector(line)

        if ins is None:
            time += 1  # time is actually the number of lines (including "API CALL .." lines)
            continue

        if debugMode:
            print '_ _ _ _\n'
            print '++ Read from trace : ' + str(ins)

        confirmedLoop = None

        # The list order is important

        for p in onGoingLoopsStacks:

            if not p.empty():
                if debugMode:
                    print '++ Test loop stack: '
                    p.display()
                if match(loopStorage, ins, p, history, time):
                    confirmedLoop = p
                    break  # As soon as we got a confirmed loop we are happy!


        if confirmedLoop is None:
            # We test if the current instruction can begin a loop
            if createLoops(loopStorage, history.possibleLoops(ins),
                           time, history):
                history.append(ins, time)  # We dont append for 1-inst loop
        else:
            # Only one confirmed loop at a time, we can clean the others
            cleanOnGoingLoops(p)
        time += 1

    f.close()

    if debugMode:
        print '\nHistory'
        history.display()

    return loopStorage


def createLoopInstance(loopStorage, body, time):

    ''' 
        Creates an instance, with the body as a instruction list.
        The time corresponds of the first instruction of the body executed.
    '''

    # Create a possible new loop with fake id

    insBody = list()
    for tins in body:
        insBody.append(tins[1])

    newLoop = loop(0x0, time, insBody)

    loopInstanceStartAddress = body[0x0][1].address

    # Is this loop already in the historic ?
    # Could be improve by using hashes + set

    for k in loopStorage.keys():
        if loopStorage[k] == newLoop:
            loopStorage[k].addInstance(time, 1, 1,
                    loopInstanceStartAddress)
            return (loopStorage[k].ID, loopStorage[k].numberOfInstances
                    - 1)

    # Otherwise register a new possible loop

    loopCounter = len(loopStorage)
    loopStorage[loopCounter] = newLoop
    loopStorage[loopCounter].ID = loopCounter

    loopStorage[loopCounter].instances[0x0].startAddress = \
        loopInstanceStartAddress

    return (loopStorage[loopCounter].ID, 0x0)


def createLoops(loopStorage,bodiesList,time,history):

    ''' 
        Create possible loops with a list of bodies. 
    '''

    global onGoingLoopsStacks

    for body in bodiesList:
        if debugMode:
            print '++ Loop creation with body :'
            for e in body:
                print '\t t:' + str(e[0x0]) + ' ins:' + str(e[1])
        
        p = stackOfLoop()
        
        (idLoop, idInstance) = createLoopInstance(loopStorage, body,
                body[0x0][0x0])

        p.push(str(idLoop) + '-' + str(idInstance))

        onGoingLoopsStacks.append(p)

        # SPECIAL CASE : 1-inst loop : 
        # It has the priority over other possible
        # loops because it's already valid ! (2 turns seen)

        if len(body) == 1:
            if debugMode:
                print 'Special Case: 1-inst loop'

            # Increment turns

            loopStorage[idLoop].instances[idInstance].turns += 1
            loopStorage[idLoop].instances[idInstance].waitFor = 0x0

            # Validate the loop

            history.suppressByTheEnd(loopStorage[idLoop].body)
            loopStorage[idLoop].instances[idInstance].valid = 1

            # No push in detectLoop()

            return 0x0

    return 1


def increment(loopStorage, p, history):

    currentLoopID = int(p.head()[:p.head().find('-')])
    currentLoopInstanceID = int(p.head()[p.head().find('-') + 1:])

    curLoop = loopStorage[currentLoopID]
    curLoopInstance = curLoop.instances[currentLoopInstanceID]

    curLoopInstance.waitFor = (curLoopInstance.waitFor + 1) % len(curLoop.body)

    # Test for a new iteration

    if curLoopInstance.waitFor == 0x0:

        curLoopInstance.turns += 1
        
        if debugMode:
            print '++ We made a turn!'

        # The first time we need to suppress two times the loop body

        if curLoopInstance.turns == 2:
            if debugMode:
                print '++ Loop validate (2 turns)'

            history.suppressByTheEnd(loopStorage[currentLoopID].body)
            history.suppressByTheEnd(loopStorage[currentLoopID].body)
            curLoopInstance.valid = 1


def closeLoop(loopStorage,p,history,time):

    currentLoop = p.pop()

    currentLoopID = int(currentLoop[:currentLoop.find('-')])
    currentLoopInstanceID = int(currentLoop[currentLoop.find('-') + 1:])

    curLoop = loopStorage[currentLoopID]
    curLoopInstance = curLoop.instances[currentLoopInstanceID]

    if curLoopInstance.turns >= 2:
        if debugMode:
            print '++ Ok for close!'

        # Record the loop instance

        curLoopInstance.close = 1
        curLoopInstance.endTime = time

        # Suppress the loop instructions from the history

        w8ForIndex = curLoopInstance.waitFor
        history.suppressByTheEnd(curLoop.body[:w8ForIndex])

        history.append(executionTrace.instruction('0', '+L' + str(currentLoopID)),time)
        return 1

    return 0x0

def match(loopStorage,ins,p,history,time):

    ''' 
        Recursive function that returns 1 if ins is awaited by a *valid*
        loop.
    '''

    currentLoopID = int(p.head()[:p.head().find('-')])
    currentLoopInstanceID = int(p.head()[p.head().find('-') + 1:])

    curLoop = loopStorage[currentLoopID]
    curLoopInstance = curLoop.instances[currentLoopInstanceID]

    w8ForIndex = curLoopInstance.waitFor
    w8ForInst = curLoop.body[w8ForIndex]

    if debugMode:
        print '++ Match fonction w8 for ' + str(w8ForInst) \
            + ' and I have ' + str(ins)

    # If the waited instruction is a loop, we have to instantiate it

    if w8ForInst.isALoop():
        if debugMode:
            print "++ I'm on a loop... I push it!"

        # Get the loop ID

        loopID = int(str(w8ForInst)[2:])

        # Create a new instance

        instanceID = loopStorage[loopID].addInstance(time, 0x0, 0x0,ins.address)
        newInstance = str(loopID) + '-' + str(instanceID)

        p.push(newInstance)

        return match(loopStorage, ins, p, history, time)
    else:
        if ins == w8ForInst:
            if debugMode:
                print '++ This is a match!'

            increment(loopStorage, p, history)

            if curLoopInstance.valid == 1 and curLoopInstance.close == 0x0:
                return 1  # success
            else:
                return 0x0
        else:
            if debugMode:
                print '++ No match at time.. ' + str(time)
            
            close = closeLoop(loopStorage, p, history, time - 1)

            if close and not p.empty():

                if debugMode:
                
                    print '++ But we have more to match'
            
                increment(loopStorage, p, history)
            
                return match(loopStorage, ins, p, history, time)
            
            else:
            
                while not p.empty():
                    closeLoop(loopStorage, p, history, time - 1)
            
                return 0x0

def cleanOnGoingLoops(p = None):

    global onGoingLoopsStacks

    if p is not None:
        onGoingLoopsStacks = list([p])
    else:
        onGoingLoopsStacks = list()




#################################
# LOOP I/O PARAMETERS
#################################

def buildLoopIOMemory(myLoopStorage, myTraceFileName):

    ''' 
        Build I/O parameters from memory. A parameter is defined as a set of
        bytes adjacent in memory *and* used (R|W) by a same instruction in a
        loop body. The actual values of these parameters will be set later 
        during the loop data flow graph building.
    '''

    for k in myLoopStorage.keys():

        myLoop = myLoopStorage[k]

        # For all instances of the loop

        for instanceCounter in myLoop.instances.keys():

            # Only take into account the valid instances

            if myLoop.instances[instanceCounter].valid == 0x0:
                continue

            model = list()
            for ins in range(0x0, len(myLoop.body)):
                model.append(list())
                model[ins].append(set())  # Read memory addresses
                model[ins].append(set())  # Written memory addresses

            writtenAddresses = set()

            insCounter = 0x0
            time = myLoop.instances[instanceCounter].startTime

            f = open(myTraceFileName, 'r')
            lineCounter = 1

            # Go to the first line

            while lineCounter != time + 1:
                f.readline()
                lineCounter += 1

            firsTurn = 1
            while time <= myLoop.instances[instanceCounter].endTime:

                myIns = executionTrace.lineConnector(f.readline())
                if myIns is None:
                    time += 1
                    continue

                # Jump over nested loops
                # The nested loop can turn a different number of times at each turn of the big loop

                if str(myLoop.body[insCounter]).startswith('+L'):

                    # Goal : move the time over the loop in the trace

                    loopId = int(str(myLoop.body[insCounter])[2:])

                    # Look for the associated instance based on its starttime

                    found = 0x0
                    for k in myLoopStorage.keys():
                        if myLoopStorage[k].ID == loopId:
                            found = 1

                            foundBis = 0x0
                            for kk in myLoopStorage[k].instances.keys():
                                if myLoopStorage[k].instances[kk].startTime \
                                    == time:

                                    # carry out the instance length in the trace

                                    lengthToJump = \
    myLoopStorage[k].instances[kk].endTime \
    - myLoopStorage[k].instances[kk].startTime + 1
                                    foundBis = 1
                                    myLoop.instances[instanceCounter].imbricatedInstanceID.append([k,
        kk])
                                    break

                            if foundBis == 0x0:
                                print 'Fail to find the instance!'
                                print 'Loop ' + str(myLoop.ID)
                                print 'We look for ' + str(loopId) \
                                    + ' at time ' + str(time)
                                return

                    if found == 0x0:
                        print 'Fail to find the loop !!!'
                        return

                    time += lengthToJump

                    lineCounter = 0x0

                    # Go to the first line

                    while lineCounter != lengthToJump - 1:
                        f.readline()
                        lineCounter += 1
                else:

                    # Read

                    count = 0x0
                    for rAddr in myIns.memoryReadAddress:
                        for b in range(0x0,
                                myIns.memoryReadSize[count]):
                            addr = int(rAddr, 16) + b

                            # Not previously written ?

                            if addr not in writtenAddresses:
                                model[insCounter][0x0].add(addr)
                        count += 1

                    # Write

                    count = 0x0
                    for wAddr in myIns.memoryWriteAddress:
                        for b in range(0x0,
                                myIns.memoryWriteSize[count]):
                            addr = int(wAddr, 16) + b
                            model[insCounter][1].add(addr)
                            writtenAddresses.add(addr)
                        count += 1

                    time += 1

                insCounter = (insCounter + 1) % len(myLoop.body)
                if insCounter == 0x0:
                    firsTurn = 0x0

            f.close()

           
            # Build input variables

            inputVar = list()
            for ins in range(0x0, len(myLoop.body)):

                if len(model[ins][0x0]) != 0x0:
                    var = variable.variable(0x0, 0x0)
                    for addr in range(min(model[ins][0x0]),
                            max(model[ins][0x0]) + 1):
                        if addr in model[ins][0x0]:
                            if var.startAddress == 0x0:
                                var.startAddress = addr
                            var.incrementSize()
                        else:

                            # Close existing var if there is one

                            if var.startAddress != 0x0:
                                inputVar.append(var)
                                var = variable.variable(0x0, 0x0)

                    # Close last one

                    if var.startAddress != 0x0:
                        inputVar.append(var)
                        var = variable.variable(0x0, 0x0)

            # Build output variables

            outputVar = list()
            for ins in range(0x0, len(myLoop.body)):

                if len(model[ins][1]) != 0x0:
                    var = variable.variable(0x0, 0x0)
                    for addr in range(min(model[ins][1]),
                            max(model[ins][1]) + 1):
                        if addr in model[ins][1]:
                            if var.startAddress == 0x0:
                                var.startAddress = addr
                            var.incrementSize()
                        else:

                            # Close existing var if there is one

                            if var.startAddress != 0x0:
                                outputVar.append(var)
                                var = variable.variable(0x0, 0x0)

                    # Close last one

                    if var.startAddress != 0x0:
                        outputVar.append(var)
                        var = variable.variable(0x0, 0x0)

            # Deal with doublons

            # Input vars

            i = 0x0
            while i < len(inputVar):
                for j in range(i + 1, len(inputVar)):
                    if inputVar[i].contains(inputVar[j]):
                        del inputVar[j]
                        i = -1
                        break
                    if inputVar[i].intersects(inputVar[j]):
                        inputVar[i] = inputVar[i].merge(inputVar[j])
                        del inputVar[j]
                        i = -1
                        break
                i += 1

            # # Output vars

            i = 0x0
            while i < len(outputVar):
                for j in range(i + 1, len(outputVar)):
                    if outputVar[i].contains(outputVar[j]):
                        del outputVar[j]
                        i = -1
                        break
                    if outputVar[i].intersects(outputVar[j]):
                        outputVar[i] = outputVar[i].merge(outputVar[j])
                        del outputVar[j]
                        i = -1
                        break
                i += 1

            myLoop.instances[instanceCounter].inputMemoryParameters = inputVar
            myLoop.instances[instanceCounter].outputMemoryParameters = outputVar


def buildLoopIORegisters(myLoopStorage, myTraceFileName):

    ''' 
        Build I/O parameters from register. Such parameters are defined as
        bytes manipulated by a same instruction in a loop body *and* in the same
        register at this moment. In contrary to memory I/O parameters, we set
        their values here.
    '''

    for k in myLoopStorage.keys():

        myLoop = myLoopStorage[k]

        # for all instances of the loop

        for instanceCounter in myLoop.instances.keys():

            # Only take into account the valid instances

            if myLoop.instances[instanceCounter].valid == 0x0:
                continue

            registerInputBytes = dict()  # addr -> value
            registerOutputBytes = dict()

            insCounter = 0x0
            time = myLoop.instances[instanceCounter].startTime

            f = open(myTraceFileName, 'r')
            lineCounter = 1

            # Go to the first line

            while lineCounter != time + 1:
                f.readline()
                lineCounter += 1

            firsTurn = 1
            while time <= myLoop.instances[instanceCounter].endTime:

                myIns = executionTrace.lineConnector(f.readline())

                if myIns is None:

                    # print "continue"

                    time += 1
                    continue

                # Jump over nested loops
                # The nested loop can turn a different number of times at each turn of the big loop

                if str(myLoop.body[insCounter]).startswith('+L'):

                    # Goal : move the time over the loop in the trace
                    # What loop ?

                    loopId = int(str(myLoop.body[insCounter])[2:])

                    # Look for the associated instance (could we make the assumption that the key == ID ?)

                    found = 0x0
                    for k in myLoopStorage.keys():
                        if myLoopStorage[k].ID == loopId:
                            found = 1

                            # Look for the instance with the right start time

                            foundBis = 0x0
                            for kk in myLoopStorage[k].instances.keys():
                                if myLoopStorage[k].instances[kk].startTime \
                                    == time:

                                    # carry out the instance length in the trace

                                    lengthToJump = \
    myLoopStorage[k].instances[kk].endTime \
    - myLoopStorage[k].instances[kk].startTime + 1
                                    foundBis = 1
                                    myLoop.instances[instanceCounter].imbricatedInstanceID.append([k,
        kk])
                                    break

                            if foundBis == 0x0:
                                print 'Fail to find the instance!'
                                print 'Loop ' + str(myLoop.ID)
                                print 'We look for ' + str(loopId) \
                                    + ' at time ' + str(time)
                                return

                    if found == 0x0:
                        print 'Fail to find the loop !!!'
                        return

                    time += lengthToJump

                    lineCounter = 0x0

                    # Go to the first line

                    while lineCounter != lengthToJump - 1:
                        f.readline()
                        lineCounter += 1
                else:

                    # Read

                    count = 0x0
                    for rReg in myIns.registersRead:
                        countAddr = 0x0
                        for addr in utilities.registersAddress(rReg):
                            if addr not in registerOutputBytes.keys():
                                registerInputBytes[addr] = \
                                    (myIns.registersReadValue[count])[countAddr
                                    * 2:countAddr * 2 + 2]
                            countAddr += 1
                        count += 1

                    # Write

                    count = 0x0
                    for wReg in myIns.registersWrite:
                        countAddr = 0x0
                        for addr in utilities.registersAddress(wReg):
                            registerOutputBytes[addr] = \
                                (myIns.registersWriteValue[count])[countAddr
                                * 2:countAddr * 2 + 2]
                            countAddr += 1
                        count += 1

                    time += 1

                insCounter = (insCounter + 1) % len(myLoop.body)
                if insCounter == 0x0:
                    firsTurn = 0x0

            f.close()

            # Input register parameters

            for reg in utilities.GPR32:
                
                # Check which parts of the reg have been used
                existL = 0x0 # AL, BL...
                existH = 0x0 # AH, BH...
                existX = 0x0 # EAX, EBX...

                if reg + '3' in registerInputBytes.keys():
                    existL = 1

                if reg + '2' in registerInputBytes.keys():
                    existH = 1

                if reg + '1' in registerInputBytes.keys():
                    existX = 1

                if existX: # 32 bytes register

                    var = variable.variable(0x0, 4, reg)

                    var.value[0x0] = registerInputBytes[reg + '0']
                    var.value[1] = registerInputBytes[reg + '1']
                    var.value[2] = registerInputBytes[reg + '2']
                    var.value[3] = registerInputBytes[reg + '3']

                    myLoop.instances[instanceCounter].inputRegisterParameters.append(var)
                    
                elif existH and existL: # 16 bytes register

                    var = variable.variable(0x0, 2, reg[1:])

                    var.value[0x0] = registerInputBytes[reg + '2']
                    var.value[1] = registerInputBytes[reg + '3']

                    myLoop.instances[instanceCounter].inputRegisterParameters.append(var)

                elif existH: # 8 bytes register (AH, BH...)

                    var = variable.variable(0x0, 1, reg[1:2] + 'h')

                    var.value[0x0] = registerInputBytes[reg + '2']
                    
                    myLoop.instances[instanceCounter].inputRegisterParameters.append(var)

                elif existL: # 8 bytes register (AL, BL...)

                    var = variable.variable(0x0, 1, reg[1:2] + 'l')

                    var.value[0x0] = registerInputBytes[reg + '3']
                    
                    myLoop.instances[instanceCounter].inputRegisterParameters.append(var)

            # Output register parameters

            for reg in utilities.GPR32:
            
                # Check which parts of the reg have been used
                existL = 0x0 # AL, BL...
                existH = 0x0 # AH, BH...
                existX = 0x0 # EAX, EBX...

                if reg + '3' in registerOutputBytes.keys():
                    existL = 1

                if reg + '2' in registerOutputBytes.keys():
                    existH = 1

                if reg + '1' in registerOutputBytes.keys():
                    existX = 1

                if existX: # 32 bytes register

                    var = variable.variable(0x0, 4, reg)

                    var.value[0x0] = registerOutputBytes[reg + '0']
                    var.value[1] = registerOutputBytes[reg + '1']
                    var.value[2] = registerOutputBytes[reg + '2']
                    var.value[3] = registerOutputBytes[reg + '3']

                    myLoop.instances[instanceCounter].outputRegisterParameters.append(var)
                    
                elif existH and existL: # 16 bytes register

                    var = variable.variable(0x0, 2, reg[1:])

                    var.value[0x0] = registerOutputBytes[reg + '2']
                    var.value[1] = registerOutputBytes[reg + '3']

                    myLoop.instances[instanceCounter].outputRegisterParameters.append(var)

                elif existH: # 8 bytes register (AH, BH...)

                    var = variable.variable(0x0, 1, reg[1:2] + 'h')

                    var.value[0x0] = registerOutputBytes[reg + '2']
                    
                    myLoop.instances[instanceCounter].outputRegisterParameters.append(var)

                elif existL: # 8 bytes register (AL, BL...)

                    var = variable.variable(0x0, 1, reg[1:2] + 'l')

                    var.value[0x0] = registerOutputBytes[reg + '3']
                    
                    myLoop.instances[instanceCounter].outputRegisterParameters.append(var)


def buildLoopIOConstants(myLoopStorage, myTraceFileName):

    ''' 
        Build constant parameters for loops, e.g. 0x42 in MOV EAX, 0x42. In
        particular, these are only input parameters. It actually only works 
        for 4-byte contants (cf. TODO list).
    '''

    constantAddr = 0x0

    for k in myLoopStorage.keys():

        myLoop = myLoopStorage[k]

        # For all instances of the loop

        for instanceCounter in myLoop.instances.keys():

            # Only take into account the valid instances

            if myLoop.instances[instanceCounter].valid == 0x0:
                continue

            constantSet = set()
            insCounter = 0x0
            time = myLoop.instances[instanceCounter].startTime

            f = open(myTraceFileName, 'r')
            lineCounter = 1

            # Go to the first line

            while lineCounter != time + 1:
                f.readline()
                lineCounter += 1

            firsTurn = 1
            while time <= myLoop.instances[instanceCounter].endTime:

                myIns = executionTrace.lineConnector(f.readline())

                if myIns is None:

                    # print "continue"

                    time += 1
                    continue

                # Jump over nested loops
                # The nested loop can turn a different number of times at each turn of the big loop

                if str(myLoop.body[insCounter]).startswith('+L'):

                    # Goal : move the time over the loop in the trace
                    # What loop ?

                    loopId = int(str(myLoop.body[insCounter])[2:])

                    # Look for the associated instance (could we make the assumption that the key == ID ?)

                    found = 0x0
                    for k in myLoopStorage.keys():
                        if myLoopStorage[k].ID == loopId:
                            found = 1

                            # Look for the instance with the right start time

                            foundBis = 0x0
                            for kk in myLoopStorage[k].instances.keys():
                                if myLoopStorage[k].instances[kk].startTime \
                                    == time:

                                    # Carry out the instance length in the trace

                                    lengthToJump = myLoopStorage[k].instances[kk].endTime \
                                                    - myLoopStorage[k].instances[kk].startTime + 1
                                    foundBis = 1
                                    myLoop.instances[instanceCounter].imbricatedInstanceID.append([k,kk])
                                    break

                            if foundBis == 0x0:
                                print 'Fail to find the instance!'
                                print 'Loop ' + str(myLoop.ID)
                                print 'We look for ' + str(loopId) \
                                    + ' at time ' + str(time)
                                return

                    if found == 0x0:
                        print 'Fail to find the loop !!!'
                        return

                    time += lengthToJump

                    lineCounter = 0x0

                    # Go to the first line

                    while lineCounter != lengthToJump - 1:
                        f.readline()
                        lineCounter += 1
                else:

                    for cte in myIns.constants:

                        if cte not in constantSet:

                            constantSet.add(cte)

                            # Due to the way we represent parameters, we have
                            # to attribute fake addresses to constant parameters. These
                            # adresses need to be unique, in order to not
                            # influence the data-flow building step.

                            var = variable.variable(constantAddr, 4)
                            var.constant = 1
                            constantAddr += 4

                            for i in range(0x0, 4):
                                var.value[i] = cte[i * 2:i * 2 + 2]

                            myLoop.instances[instanceCounter].constantParameter.append(var)

                    time += 1

############################
# DEBUG FUNCTIONS
############################

def pydotGraphLoopStorage(loopStorage, name, mode=0x0):
    
    ''' 
        Produces a graph whose loops and their parameters are the nodes,
        whereas edges shows variable intersection.
        mode : 0 for full display, 1 for light (only loop ID)
    '''

    # 0. Graph

    graph = pydot.Dot(graph_type='digraph')
    id = 0x0

    inputVarLoop = set()
    outputVarLoop = set()

    # For each loop instances

    for l in loopStorage.keys():

        for instan in loopStorage[l].instances.keys():

            # Only valid instance

            myLoopInstance = loopStorage[l].instances[instan]
            if myLoopInstance.valid == 1:

                # 1. Create Loop Node

                label = ''
                if mode == 0x0:
                    label = \
                        '<<table border="0" cellborder="0" cellpadding="3" bgcolor="white"><tr><td bgcolor="black" align="center" colspan="1"><font color="white">LOOP ' \
                        + str(loopStorage[l].ID) + '-' \
                        + str(myLoopInstance.ID) \
                        + ' ++ Start address : 0x' \
                        + myLoopInstance.startAddress \
                        + '</font></td></tr>'
                    index = 0x0
                    for ins in loopStorage[l].body:

                        label += '<tr><td align="left">' + ins.x86ASM

                        if len(ins.apiCall) != 0x0:
                            label += ' ' + ins.apiCall + '()'

                        label += '</td></tr>'

                        index += 1
                    label += '</table>>'
                else:
                    label = str(loopStorage[l].ID) + '-' \
                        + str(myLoopInstance.ID) \
                        + ' Start address : 0x' \
                        + myLoopInstance.startAddress

                graph.add_node(pydot.Node(id, label=label,
                               fontname='Consolas', shape='Mrecord'))

                edge = pydot.Edge(id, id, color='blue',
                                  fontname='Consolas')
                edge.set_label(str(myLoopInstance.turns))
                graph.add_edge(edge)

                myLoopInstance.pydotNodeID = id

                id += 1

                # 2. Create Input Var Node

                for inputVar in myLoopInstance.inputMemoryParameters:
                    graph.add_node(pydot.Node(id,
                                   label=hex(inputVar.startAddress)
                                   + ':' + str(inputVar.size),
                                   style='filled', fillcolor='#970000',
                                   fontname='Consolas'))

                    edge = pydot.Edge(id, myLoopInstance.pydotNodeID)
                    inputVar.pydotNodeID = id
                    inputVar.loopInstanceID = loopStorage[l].ID * 100 \
                        + myLoopInstance.ID
                    graph.add_edge(edge)
                    inputVarLoop.add(inputVar)
                    id += 1

                # regs

                for inputRegVar in myLoopInstance.inputRegisterParameters:
                    graph.add_node(pydot.Node(id, label=' '
                                   + inputRegVar.registerName + ':'
                                   + str(inputRegVar.size) + ' ',
                                   style='filled', fillcolor='#970000',
                                   fontname='Consolas'))

                    edge = pydot.Edge(id, myLoopInstance.pydotNodeID)
                    inputRegVar.pydotNodeID = id
                    inputRegVar.loopInstanceID = loopStorage[l].ID \
                        * 100 + myLoopInstance.ID
                    graph.add_edge(edge)



                    id += 1

                # 2. Create Ouput Var Node

                for outputVar in myLoopInstance.outputMemoryParameters:

                    
                    graph.add_node(pydot.Node(id,
                                   label=hex(outputVar.startAddress)
                                   + ':' + str(outputVar.size),
                                   style='filled', fillcolor='#976856',
                                   fontname='Consolas'))

                    edge = pydot.Edge(myLoopInstance.pydotNodeID, id)
                    outputVar.pydotNodeID = id
                    outputVar.loopInstanceID = loopStorage[l].ID * 100 \
                        + myLoopInstance.ID
                    graph.add_edge(edge)
                    outputVarLoop.add(outputVar)
                    id += 1

                # regs

                for outputRegVar in myLoopInstance.outputRegisterParameters:
                    graph.add_node(pydot.Node(id, label=' '
                                   + outputRegVar.registerName + ':'
                                   + str(outputRegVar.size) + ' ',
                                   style='filled', fillcolor='#976856',
                                   fontname='Consolas'))

                    edge = pydot.Edge(myLoopInstance.pydotNodeID, id)
                    outputRegVar.pydotNodeID = id
                    outputRegVar.loopInstanceID = loopStorage[l].ID \
                        * 100 + myLoopInstance.ID
                    graph.add_edge(edge)

                    id += 1

    # Loop nesting :

    for l in loopStorage.keys():
        for instan in loopStorage[l].instances.keys():

            # Only valid instance

            myLoopInstance = loopStorage[l].instances[instan]

            if myLoopInstance.valid == 1:

                # 3. Create links with nested loops

                for ins in loopStorage[l].body:
                    if str(ins).startswith('+L'):
                        loopID = int(str(ins)[2:])
                        for imbricatedInstance in \
                            myLoopInstance.imbricatedInstanceID:
                            if imbricatedInstance[0x0] != loopID:
                                continue
                            idSmallLoop = \
                                loopStorage[imbricatedInstance[0x0]].instances[imbricatedInstance[1]].pydotNodeID
                            edge = \
                                pydot.Edge(myLoopInstance.pydotNodeID,
                                    idSmallLoop, color='red')
                            graph.add_edge(edge)

    # Link between same var

    for ov in outputVarLoop:
        for iv in inputVarLoop:

            # Broad notion of data-flow

            if ov.contains(iv) or iv.contains(ov):
                if ov.loopInstanceID != iv.loopInstanceID:
                    edge = pydot.Edge(ov.pydotNodeID, iv.pydotNodeID,
                            color='blue')
                    graph.add_edge(edge)
                    
    # 0.5s for jpeg
    # 1.5s for png
    # 0.1 for dot

    graph.write_dot(name + '.dot')
    graph.write_png(name + '.png')


def displayOnGoingLoops():

    global onGoingLoopsStacks

    print '\nonGoingLoopsStacks:'
    number = 0x0
    for p in onGoingLoopsStacks:
        print 'Stack %d ' % number
        number += 1
        p.display()
