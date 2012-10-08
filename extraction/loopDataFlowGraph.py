#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# Aligot project

# A Loop Data Flow Graph (LDFG) is a graph whose nodes are loops, and edges
# represent data flow relationships between such loops.
# Each connected component of the graph is named a Loop Data Flow (LDF).

# Copyright, licence: who cares?
# ----------------------------------------------

import copy
import pydot
import itertools
import networkx as nx

# Aligot modules

import loops
import executionTrace
import utilities

 

class LoopDataFlow: 

    '''
        Connected component of the LDFG.
    '''

    def __init__(self, ID, loopInstance):

        self.ID = ID 

        self.startTime = loopInstance.startTime
        self.endTime = loopInstance.endTime

        self.loopInstanceList = [loopInstance]  # List of instance, ordered by starttime
        self.inputParameters = list()
        self.outputParameters = list()
        self.valid = 1

        # To build the i/o values

        self.WALFI = dict()  # We Are Looking For Input
        self.WALFO = dict()  # We Are Looking For Output

    def display(self):

        print '-----------------------------------'
        print 'Loop Data Flow ' + str(self.ID)

        print str(len(self.loopInstanceList)) + ' loop instances'

        print 'Start time : ' + str(self.startTime),
        print ' (start address: ' + self.loopInstanceList[0].startAddress + ')'
        print 'End time : ' + str(self.endTime)

        print 'Input Parameters:'
        for iv in self.inputParameters:
            iv.display(1) 
            print " | ",


        print '\nOutput Parameters:'
        for ov in self.outputParameters:
            ov.display(1)
            print " | ",


        print '\n-----------------------------------'

    def merge(self, otherLDF):

        ''' 
            We merge the two LDFs by keeping this one, extending it with
            otherLDF, and finally disable otherLDF.         
        '''

        for loopIns1 in otherLDF.loopInstanceList:

            # We need to keep the start time ordering

            if loopIns1.startTime > self.loopInstanceList[-1].startTime:
                self.loopInstanceList.insert(len(self.loopInstanceList),
                        loopIns1)
            else:
                posToInsert = 0
                for loopIns2 in self.loopInstanceList:
                    if loopIns1.startTime < loopIns2.startTime:
                        self.loopInstanceList.insert(posToInsert,
                                loopIns1)
                        break
                    posToInsert += 1

        self.startTime = self.loopInstanceList[0].startTime
        self.endTime = self.loopInstanceList[-1].endTime

        otherLDF.valid = 0


def dumpResults(graphStorage, fileName='results.txt', inTrace=''):
    
    ''' 
        Create the final result file. Each line contains the I/O parameter
        values for one LDF. 
    '''

    out = open(fileName, 'w')

    # Header building

    out.write('Aligot - Parameters extracted for each LDF')
    if len(inTrace) != 0:
        out.write(' from ' + inTrace + '\n')
    out.write('All values are in hexadecimal. Format: {address|R for registers|C for static constants}|value.')
    out.write('Input/output parameters are separated by \':\'.')
    out.write('The values are padded with zero to have the correct length.\n\n')

    for k in graphStorage.keys():
        currentLDF = graphStorage[k]
        line = ''
        for iv in currentLDF.inputParameters:
            val = ''

            if iv.registerName != '':
                val += 'R|'
            elif iv.constant == 1:
                val += 'C|'
            else:
                val += hex(iv.startAddress)[2:] + '|'
            
            for byte in range(0, iv.size):
                val += iv.value[byte]
            line += val + ','

        line = line[:-1] + ':'

        for ov in currentLDF.outputParameters:
            val = ''

            if ov.registerName != '':
                val += 'R|'
            elif ov.constant == 1:
                val += 'C|'
            else:
                val += hex(ov.startAddress)[2:] + '|'

            for byte in range(0, ov.size):
                val += ov.value[byte]
            line += val + ','

        if line[-1] != ':':
            line = line[:-1] + '\n'
        else:
            line += '\n'

        out.write(line)

    out.close()

def display(graphStorage):

    for k in graphStorage.keys():
        graphStorage[k].display()


def pydotGraph(graphStorage,name, limit=10):

    '''
        limit indicates the maximal number of graphs to produce.
    '''

    # For each LDF

    for k in graphStorage.keys():

        currentLDF = graphStorage[k]

        if currentLDF.valid == 0:
            continue

        graph = pydot.Dot(graph_type='digraph')
        nodeId = 0
        label = 'LDF ' + str(k)
        label += '\n' + str(len(currentLDF.loopInstanceList)) + ' LI'
        label += ' - SA:' + currentLDF.loopInstanceList[0].startAddress

        # The LDF node

        graph.add_node(pydot.Node(
            nodeId,
            label=label,
            width='3',
            height='1.5',
            fontsize='20',
            style='filled',
            color='lightgrey',
            fontname='Consolas',
            shape='Mrecord',
            ))

        ldfID = nodeId
        nodeId += 1

        # The input vars

        for iv in currentLDF.inputParameters:

            label = '{'

            if iv.registerName == '':
                label += hex(iv.startAddress) + ':' + str(iv.size)
            else:
                label += iv.registerName + ':' + str(iv.size)

            label += ' | '

            valueSize = 0
            for ivP in iv.value.keys():
                if valueSize == 16:
                    label+="..."
                    break
                label += iv.value[ivP]
                valueSize += 1

            label += ' }'

            graph.add_node(pydot.Node(
                nodeId,
                label=label,
                style='filled',
                fillcolor='chocolate1',
                shape='record',
                fontname='Consolas',
                fontsize='20',
                ))

            edge = pydot.Edge(nodeId, ldfID, width='5',
                              color='chocolate1', penwidth='3')
            nodeId += 1

            graph.add_edge(edge)

        # The output vars

        for ov in currentLDF.outputParameters:

            label = '{'

            if ov.registerName == '':
                label += hex(ov.startAddress) + ':' + str(ov.size)
            else:
                label += ov.registerName + ':' + str(ov.size)

            label += ' | '
            valueSize = 0
            for ovP in ov.value.keys():
                if valueSize == 16:
                    label+="..."
                    break
                label += ov.value[ovP]
                valueSize += 1

            label += ' }'

            graph.add_node(pydot.Node(
                nodeId,
                label=label,
                style='filled',
                fillcolor='deepskyblue1',
                shape='record',
                fontname='Consolas',
                fontsize='20',
                ))

            edge = pydot.Edge(ldfID, nodeId, color='deepskyblue1',
                              penwidth='3')
            nodeId += 1
            graph.add_edge(edge)

        graph.write_png(name + str(k) + '.png')
        graph.write_dot(name + str(k) + '.dot')

        # return

        if k == limit:
            print '** Limit reached **'
            return


def garbageCollector(graphStorage):

    ''' 
        Remove invalid LDFs
    '''

    for k in graphStorage.keys():
        currentLDF = graphStorage[k]

        if currentLDF.valid == 0:
            graphStorage.pop(k)

def garbageCollectorUselessLDF(graphStorage):

    '''
        Remove LDFs without input or output parameters.
    '''

    for k in graphStorage.keys():
        currentLDF = graphStorage[k]

        if (len(currentLDF.inputParameters) == 0) & (len(currentLDF.loopInstanceList[0].inputRegisterParameters) == 0) \
            or (len(currentLDF.outputParameters) == 0) & (len(currentLDF.loopInstanceList[-1].outputRegisterParameters) == 0):

            graphStorage.pop(k)


def build(loopStorage, allSubgraphs=False, singleInsLoop = False):

    '''
        Create the LDFG by testing the following binary relation between loop instances:
        
        L1 and L2 are connected iff:
            -  L1 started before L2 in the execution trace 
            -  OUT(L1) intersects IN(L2)

        As a result, graphStorage is filled with the loop data flows
        (connected components of the graph, or any subgraph, depending on the argument
        allSubgraph)          
    '''

    graphStorage = dict()

    # Sort loop instances by time

    sortedLoopInstances = list()  # List of [loopID,InstanceID]

    for loopKey in loopStorage.keys():
        myLoop = loopStorage[loopKey]

        if len(myLoop.body) == 1 and not singleInsLoop:
            print 'WARNING: 1 instruction loop ignored'
            continue

        # Insertion sort on loop instances
        for instanceKey in myLoop.instances.keys():

            myLoopInstance = myLoop.instances[instanceKey]
            cursor = 0
            insertionDone = 0

            for element in sortedLoopInstances:

                loopID = element[0]
                instanceID = element[1]

                if loopStorage[loopID].instances[instanceID].startTime \
                    > myLoopInstance.startTime:

                    sortedLoopInstances.insert(cursor, [loopKey, instanceKey])
                    insertionDone = 1
                    break

                cursor += 1

            if insertionDone == 0:
                sortedLoopInstances.append([loopKey, instanceKey])

    # Graph building
    # Each node is an index in the sortedLoopInstances list

    G = nx.DiGraph()
    for i in range(0, len(sortedLoopInstances)):

        G.add_node(i)

        curLoopID = sortedLoopInstances[i][0]
        curLoopInstanceID = sortedLoopInstances[i][1]
        curLoopInstance = loopStorage[curLoopID].instances[curLoopInstanceID]

        for j in range(0, i):

            prevLoopID = sortedLoopInstances[j][0]
            prevLoopInstanceID = sortedLoopInstances[j][1]
            prevLoopInstance = loopStorage[prevLoopID].instances[prevLoopInstanceID]

            for outputParam in prevLoopInstance.outputMemoryParameters:
                for inputParam in curLoopInstance.inputMemoryParameters:

                    # Test data flow relationship
                    if outputParam.contains(inputParam) \
                        | inputParam.contains(outputParam) \
                        | inputParam.intersects(outputParam):

                        G.add_edge(j,i)

    # Find connected components as strings "-NodeID1-NodeID2-..."
    connectedComponents = set()

    if allSubgraphs:

        # We add all possible subgraphs to the connected components

        for n in G.nodes():
            pathsToDo = set()
            pathsToDo.add('-' + str(n))

            while len(pathsToDo) != 0:

                pathsDone = set()
                pathsCreated = set()

                for p in pathsToDo:
                    connectedComponents.add(p)
                    pathsDone.add(p)
                    lastNode = p[p.rfind('-') + 1:]

                    for v in G.neighbors(lastNode):
                        theNewPath = p + '-' + str(v)
                        pathsCreated.add(theNewPath)

                pathsToDo = pathsToDo.union(pathsCreated)
                pathsToDo = pathsToDo.difference(pathsDone)
    else:

        # Default mode: only (weakly) connected component are considered

        for weakConnectedComponent in nx.weakly_connected_components(G):
            cc = '-' + str(weakConnectedComponent[0])
            for node in weakConnectedComponent[1:]:
                cc = cc + '-' + str(node)
            connectedComponents.add(cc)

    # Create one LDF for each connected component

    for cc in connectedComponents:
        loopInstancePath = cc.split('-')[1:]

        firstLoopID = sortedLoopInstances[int(loopInstancePath[0])][0]
        firstLoopInstanceID = sortedLoopInstances[int(loopInstancePath[0])][1]
        firstLoopInstance = loopStorage[firstLoopID].instances[firstLoopInstanceID]

        currentLDF = LoopDataFlow(len(graphStorage.keys()), firstLoopInstance)
        graphStorage[len(graphStorage.keys())] = currentLDF

        for loopInstanceIDs in loopInstancePath[1:]:

            curLoopID = sortedLoopInstances[int(loopInstanceIDs)][0]
            curLoopInstanceID = sortedLoopInstances[int(loopInstanceIDs)][1]
            curLoopInstance = loopStorage[curLoopID].instances[curLoopInstanceID]

            currentLDF.merge(LoopDataFlow(0, curLoopInstance))

    return graphStorage

def buildIO(graphStorage):

    '''         
        Define LDF input-output parameters. Memory parameter values are not collected
        there (see assignIOValues())     
    '''

    for ldfKey in graphStorage.keys():
        currentLDF = graphStorage[ldfKey]

        inputRegisters = set()  # Already assigned input registers

        for i in range(0, len(currentLDF.loopInstanceList)):
            loopIns = currentLDF.loopInstanceList[i]

            # Input parameters

            for inputParam in loopIns.inputMemoryParameters:

                linkFound = 0
                for j in range(0, i):
                    prevLoopIns = currentLDF.loopInstanceList[j]

                    for outputParam in prevLoopIns.outputMemoryParameters:
                        if outputParam.contains(inputParam) \
                            | inputParam.contains(outputParam) \
                            | inputParam.intersects(outputParam):
                            linkFound = 1
                            break

                    if linkFound:
                        break

                if linkFound == 0:
                    currentLDF.inputParameters.append(inputParam)

            for inputRegVar in loopIns.inputRegisterParameters:
                if inputRegVar.registerName not in inputRegisters:
                    inputRegisters.add(inputRegVar.registerName)
                    currentLDF.inputParameters.append(inputRegVar)

            for cte in loopIns.constantParameter:
                currentLDF.inputParameters.append(cte)

            # Output parameters

            for outputParam in loopIns.outputMemoryParameters:

                linkFound = 0
                for j in range(i + 1,
                               len(currentLDF.loopInstanceList)):
                    futureLoopIns = currentLDF.loopInstanceList[j]

                    for inputParam in futureLoopIns.inputMemoryParameters:
                        if outputParam.contains(inputParam) \
                            | inputParam.contains(outputParam) \
                            | inputParam.intersects(outputParam):
                            linkFound = 1
                            break

                    if linkFound:
                        break

                if linkFound == 0:

                    # No doublons

                    currentLDF.outputParameters.append(outputParam)

            # Parameter doublons (loops belonging to the same LDF
            # can have same or intersecting input parameters)

            i = 0
            while i < len(currentLDF.inputParameters):
                for j in range(i + 1,
                               len(currentLDF.inputParameters)):
                    if currentLDF.inputParameters[i].contains(currentLDF.inputParameters[j]):
                        del currentLDF.inputParameters[j]
                        i = -1
                        break
                    if currentLDF.inputParameters[i].intersects(currentLDF.inputParameters[j]):
                        currentLDF.inputParameters[i] = currentLDF.inputParameters[i].merge(currentLDF.inputParameters[j])
                        del currentLDF.inputParameters[j]
                        i = -1
                        break
                i += 1

            i = 0
            while i < len(currentLDF.outputParameters):
                for j in range(i + 1,
                               len(currentLDF.outputParameters)):
                    if currentLDF.outputParameters[i].contains(currentLDF.outputParameters[j]):
                        del currentLDF.outputParameters[j]
                        i = -1
                        break
                    if currentLDF.outputParameters[i].intersects(currentLDF.outputParameters[j]):
                        currentLDF.outputParameters[i] = currentLDF.outputParameters[i].merge(currentLDF.outputParameters[j])
                        del currentLDF.outputParameters[j]
                        i = -1
                        break
                i += 1

        # Output registers: only the last loop instance
        
        for outputRegVar in \
            currentLDF.loopInstanceList[-1].outputRegisterParameters:
            currentLDF.outputParameters.append(outputRegVar)


def assignIOValues(graphStorage, myTraceFileName):

    '''
        Collect values for I/O *memory* parameters
        (registers already have their values)
    '''

    # Init the start and end time for easy research

    startTimeLDF = dict()  # time -> LDF
    for ldfKey in graphStorage.keys():
        currentLDF = graphStorage[ldfKey]

        if currentLDF.startTime not in startTimeLDF.keys():
            startTimeLDF[currentLDF.startTime] = set()

        startTimeLDF[currentLDF.startTime].add(currentLDF)

    endTimeLDF = dict()  # time -> LDF
    for ldfKey in graphStorage.keys():
        currentLDF = graphStorage[ldfKey]
        if currentLDF.endTime not in endTimeLDF.keys():
            endTimeLDF[currentLDF.endTime] = set()

        endTimeLDF[currentLDF.endTime].add(currentLDF)  # ref

    # Collect values

    ldfIDs = set()
    currentLDF = dict()

    time = 0
    f = open(myTraceFileName, 'r')

    for line in f:

        ins = executionTrace.lineConnector(line)
        if ins is None:
            time += 1
            continue

        if time in startTimeLDF.keys():

            for startingLDF in startTimeLDF[time]:

                ldfIDs.add(startingLDF.ID)
                currentLDF[startingLDF.ID] = startingLDF

                # Build the set of input bytes

                for iv in startingLDF.inputParameters:

                    # Registers AND constants have already their values

                    if iv.registerName == '' and iv.constant == 0:
                        for c in range(0, iv.size):
                            addr = iv.startAddress + c
                            startingLDF.WALFI[addr] = 'U'  # Undefined value

                # Build the set of output bytes

                for ov in startingLDF.outputParameters:

                    # Registers have already their values

                    if ov.registerName == '':
                        for c in range(0, ov.size):
                            addr = ov.startAddress + c
                            startingLDF.WALFO[addr] = 'U'  # Undefined value

        if len(ldfIDs) != 0:

            for currentLDFID in ldfIDs:

                count = 0
                for rAddr in ins.memoryReadAddress:
                    for indexByte in range(0,
                            ins.memoryReadSize[count]):
                        addrReadByte = int(rAddr, 16) + indexByte  # int
                        
                        if addrReadByte in currentLDF[currentLDFID].WALFI.keys():

                            # First time it is read, it gives its final value
                            if currentLDF[currentLDFID].WALFI[addrReadByte] == 'U':
                                valueReadByte = (ins.memoryReadValue[count])[indexByte* 2:indexByte * 2 + 2]
                                currentLDF[currentLDFID].WALFI[addrReadByte] = valueReadByte

                    count += 1

                count = 0
                for wAddr in ins.memoryWriteAddress:
                    for indexByte in range(0, ins.memoryWriteSize[count]):

                        addrWriteByte = int(wAddr, 16) + indexByte  # int

                        # Each time it is written, it updates its value

                        if addrWriteByte in currentLDF[currentLDFID].WALFO.keys():
                            valueWriteByte = (ins.memoryWriteValue[count])[indexByte* 2:indexByte * 2 + 2]
                            currentLDF[currentLDFID].WALFO[addrWriteByte] = valueWriteByte
                    count += 1

        if time in endTimeLDF.keys():

            for endingLDF in endTimeLDF[time]:

                # Copy the collected values back in the input variables

                for iv in endingLDF.inputParameters:
                    if iv.registerName == '' and iv.constant == 0:
                        for c in range(0, iv.size):

                            if endingLDF.WALFI[iv.startAddress + c] == 'U':
                                print 'ERROR - A value missed ?! (r)'
                                return

                            iv.value[c] = endingLDF.WALFI[iv.startAddress + c]

                # Copy the collected values back in the output variables

                for ov in endingLDF.outputParameters:
                    if ov.registerName == '':
                        for c in range(0, ov.size):

                            if endingLDF.WALFO[ov.startAddress + c] == 'U':
                                print 'ERROR - A value missed ?! (w)'
                                return

                            ov.value[c] = endingLDF.WALFO[ov.startAddress + c]

                ldfIDs.remove(endingLDF.ID)

        time += 1

    f.close()
