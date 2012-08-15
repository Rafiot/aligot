#!/usr/bin/python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# Aligot project

# A loop data flow graph (LDFG) is a graph whose nodes are loops, and edges
# represent data flow relationships between such loops.

# Copyright, licence: who cares?
# ----------------------------------------------

import copy
import pydot
import itertools
import networkx as nx
import matplotlib.pyplot as plt

# These are my shit!

import loops
import executionTrace
import utilities

LdfgDataBase = dict()
LdfgID = 0


class LDFG:

    def __init__(self, ID, loopInstance):

        self.ID = ID  # Key in LdfgDataBase

        self.startTime = loopInstance.startTime
        self.endTime = loopInstance.endTime

        self.loopInstanceList = [loopInstance]  # List of instance, ordered by starttime
        self.inputBasicVar = list()
        self.outputBasicVar = list()
        self.valid = 1

        # To build the i/o values

        self.WALFI = dict()  # We Are Looking For Input
        self.WALFO = dict()  # We Are Looking For Output

    def display(self):

        print '-----------------------------------'
        print 'Loop data flow graph'

        print str(len(self.loopInstanceList)) + ' loop instances'

        print 'Start time : ' + str(self.startTime)
        print 'End time : ' + str(self.endTime)

        print 'Input Basic Var:'
        for iv in self.inputBasicVar:
            iv.display(1)

        # Display input register of the first loop instance
        #         output registers of the last loop instance

        print '\nInput registers:'
        firstIns = self.loopInstanceList[0]
        for ir in firstIns.inputRegisterVar:
            ir.display(1)

        print '\nOutput Basic Var:'
        for ov in self.outputBasicVar:
            ov.display(1)

        print '\nOutput registers:'
        LastIns = self.loopInstanceList[-1]
        for outr in firstIns.outputRegisterVar:
            outr.display(1)

        print ''

    def merge(self, otherLDFG):

        # We keep this LDFG, extend it with otherLDFG, and disable otherLDFG

        for loopIns1 in otherLDFG.loopInstanceList:

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

        otherLDFG.valid = 0


def dumpResults(fileName='results.txt', inTrace=''):
    
    ''' Create the final result file. Each line contains the I/O parameter
        values for one extracted LDFG. '''

    global LdfgDataBase

    out = open(fileName, 'w')

    # Header building

    out.write('Aligot - Parameters extracted for each LDFG')
    if len(inTrace) != 0:
        out.write(' from ' + inTrace + '\n')
    out.write('Format: \"input parameter 1,input parameter 2:output paramter1,output parameter2\"\n\n')

    for k in LdfgDataBase.keys():
        myLDFG = LdfgDataBase[k]
        line = ''
        for iv in myLDFG.inputBasicVar:
            val = ''
            for byte in range(0, iv.size):
                val += iv.value[byte]
            line += val + ','

        line = line[:-1] + ':'

        for ov in myLDFG.outputBasicVar:
            val = ''
            for byte in range(0, ov.size):
                val += ov.value[byte]
            line += val + ','

        if line[-1] != ':':
            line = line[:-1] + '\n'
        else:
            line += '\n'

        out.write(line)


def graphLdfgDataBase(name):

    global LdfgDataBase

    # We do not graph everyone

    limit = 10

    # For each LDFG

    for k in LdfgDataBase.keys():

        currentLDFG = LdfgDataBase[k]

        if currentLDFG.valid == 0:
            continue

        graph = pydot.Dot(graph_type='digraph')
        nodeId = 0
        label = 'LDFG ' + str(k)
        label += '\n' + str(len(currentLDFG.loopInstanceList)) + ' LI'

        # The LDFG node

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

        curLdfgID = nodeId
        nodeId += 1

        # The input vars

        for iv in currentLDFG.inputBasicVar:

            label = '{'

            if iv.registerName == '':
                label += hex(iv.startAddress) + ':' + str(iv.size)
            else:
                label += iv.registerName + ':' + str(iv.size)

            label += ' | '

            valueSize = 0
            for ivP in iv.value.keys():
                if valueSize == 16:
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

            edge = pydot.Edge(nodeId, curLdfgID, width='5',
                              color='chocolate1', penwidth='3')
            nodeId += 1

            graph.add_edge(edge)

        # The output vars

        for ov in currentLDFG.outputBasicVar:

            label = '{'

            if ov.registerName == '':
                label += hex(ov.startAddress) + ':' + str(ov.size)
            else:
                label += ov.registerName + ':' + str(ov.size)

            label += ' | '
            valueSize = 0
            for ovP in ov.value.keys():
                if valueSize == 16:
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

            edge = pydot.Edge(curLdfgID, nodeId, color='deepskyblue1',
                              penwidth='3')
            nodeId += 1
            graph.add_edge(edge)

        graph.write_png(name + str(k) + '.png')
        graph.write_dot(name + str(k) + '.dot')

        # return

        if k == limit:
            print '** Limit reached **'
            return


# Remove invalid algos, and without input or output

def garbageCollectorLDFG():

    global LdfgDataBase

    for k in LdfgDataBase.keys():
        currentLDFG = LdfgDataBase[k]

        if currentLDFG.valid == 0:
            LdfgDataBase.pop(k)
        elif (len(currentLDFG.inputBasicVar) == 0) \
            & (len(currentLDFG.loopInstanceList[0].inputRegisterVar)
               == 0) or (len(currentLDFG.outputBasicVar) == 0) \
            & (len(currentLDFG.loopInstanceList[-1].outputRegisterVar)
               == 0):

            LdfgDataBase.pop(k)


def buildLDFG(ls, myTraceFileName, allPossiblePaths=0):

    global LdfgDataBase
    global LdfgID

    # 1. Sort the loop instance by time

    sortedLoops = list()  # List of [loopID,IntanceID,0] where 0 stands for no LDFG associated yet

                            # WARNING: the IDs use there are the dict keys... (probably the same that the "real" IDs though)

    for k in ls.keys():
        myLoop = ls[k]

        # For all instances of the loop

        for instanceCounter in myLoop.instances.keys():

            myLoopInstance = myLoop.instances[instanceCounter]

            # Only take into account the valid instances

            if myLoopInstance.valid == 0:
                continue

            # TODO: SET AN ARGUMENT FOR THAT

            if len(myLoop.body) == 1:
                print 'WARNING: 1 instruction loop ignored'
                continue

            cursor = 0
            insertionDone = 0
            for element in sortedLoops:
                loopID = element[0]
                instanceID = element[1]

                if ls[loopID].instances[instanceID].startTime \
                    > myLoopInstance.startTime:

                    # insertion

                    sortedLoops.insert(cursor, [k, instanceCounter, 0])
                    insertionDone = 1
                    break
                cursor += 1

            if insertionDone == 0:
                sortedLoops.append([k, instanceCounter, 0])

    # 2.1 LDFG creation

    # Construct graph

    G = nx.DiGraph()

    for i in range(0, len(sortedLoops)):

        G.add_node(str(sortedLoops[i][0]) + ':'
                   + str(sortedLoops[i][1]))

        curLoopInstance = \
            ls[sortedLoops[i][0]].instances[sortedLoops[i][1]]

        for j in range(0, i):
            previousLoopInstance = \
                ls[sortedLoops[j][0]].instances[sortedLoops[j][1]]
            for outputVar in previousLoopInstance.outputBasicVar:
                for inputVar in curLoopInstance.inputBasicVar:

                    if outputVar.contains(inputVar) \
                        | inputVar.contains(outputVar) \
                        | inputVar.intersects(outputVar):

                        G.add_edge(str(sortedLoops[j][0]) + ':'
                                   + str(sortedLoops[j][1]),
                                   str(sortedLoops[i][0]) + ':'
                                   + str(sortedLoops[i][1]))

    allPaths = set()

    if allPossiblePaths:

    # Each path in ze graph is a LDFG
    # The graph is a DAG, we enumerate all possible paths...

        for n in G.nodes():
            pathsToDo = set()
            pathsToDo.add('-' + str(n))

            while len(pathsToDo) != 0:

                pathsDone = set()
                pathsCreated = set()

                for p in pathsToDo:
                    allPaths.add(p)
                    pathsDone.add(p)
                    lastNode = p[p.rfind('-') + 1:]

                    for v in G.neighbors(lastNode):
                        theNewPath = p + '-' + str(v)
                        pathsCreated.add(theNewPath)

                pathsToDo = pathsToDo.union(pathsCreated)
                pathsToDo = pathsToDo.difference(pathsDone)
    else:

        # Default mode: only (weakly) connected component We collect paths not
        # necessarily in the time order, but the next phase will build
        # LDFG with the correct ordering (thanks to merge())

        for weakConnectedComponent in nx.weakly_connected_components(G):
            path = '-' + weakConnectedComponent[0]
            for node in weakConnectedComponent[1:]:
                path = path + '-' + node
            allPaths.add(path)

    # Create a LDFG for each path

    for path in allPaths:
        loopInstancePath = path.split('-')[1:]

        # First loop instance
        # TODO: REWRITE THIS SHIT

        firstLoopInstance = \
            ls[int((loopInstancePath[0])[:loopInstancePath[0].find(':'
               )])].instances[int((loopInstancePath[0])[loopInstancePath[0].find(':'
                              ) + 1:])]

        currentLDFG = LDFG(LdfgID, firstLoopInstance)
        LdfgDataBase[LdfgID] = currentLDFG
        LdfgID += 1

        for loopInstanceIDs in loopInstancePath[1:]:
            curLoopInstance = \
                ls[int(loopInstanceIDs[:loopInstanceIDs.find(':'
                   )])].instances[int(loopInstanceIDs[loopInstanceIDs.find(':'
                                  ) + 1:])]
            currentLDFG.merge(LDFG(0, curLoopInstance))

    # 3. Define LDFG input-output basic variable

    for k in LdfgDataBase.keys():
        currentLDFG = LdfgDataBase[k]

        if currentLDFG.valid == 1:

            inputRegisters = set()  # Already assigned input registers

            for i in range(0, len(currentLDFG.loopInstanceList)):
                loopIns = currentLDFG.loopInstanceList[i]

                # Deal with *memory* input vars

                for inputVar in loopIns.inputBasicVar:

                    linkFound = 0
                    for j in range(0, i):
                        prevLoopIns = currentLDFG.loopInstanceList[j]

                        for outputVar in prevLoopIns.outputBasicVar:
                            if outputVar.contains(inputVar) \
                                | inputVar.contains(outputVar) \
                                | inputVar.intersects(outputVar):
                                linkFound = 1
                                break

                        if linkFound:
                            break

                    if linkFound == 0:
                        currentLDFG.inputBasicVar.append(inputVar)

                for inputRegVar in loopIns.inputRegisterVar:
                    if inputRegVar.registerName not in inputRegisters:
                        inputRegisters.add(inputRegVar.registerName)
                        currentLDFG.inputBasicVar.append(inputRegVar)

                for cte in loopIns.constantsVar:
                    currentLDFG.inputBasicVar.append(cte)

                # Deal with output vars

                for outputVar in loopIns.outputBasicVar:

                    linkFound = 0
                    for j in range(i + 1,
                                   len(currentLDFG.loopInstanceList)):
                        futureLoopIns = currentLDFG.loopInstanceList[j]

                        for inputVar in futureLoopIns.inputBasicVar:
                            if outputVar.contains(inputVar) \
                                | inputVar.contains(outputVar) \
                                | inputVar.intersects(outputVar):
                                linkFound = 1
                                break

                        if linkFound:
                            break

                    if linkFound == 0:

                        # No doublons

                        currentLDFG.outputBasicVar.append(outputVar)

                # Input vars doublons (loops belonging to the same LDFG
                # can have same or intersecting input variables)

                i = 0
                while i < len(currentLDFG.inputBasicVar):
                    for j in range(i + 1,
                                   len(currentLDFG.inputBasicVar)):
                        if currentLDFG.inputBasicVar[i].contains(currentLDFG.inputBasicVar[j]):
                            del currentLDFG.inputBasicVar[j]
                            i = -1
                            break
                        if currentLDFG.inputBasicVar[i].intersects(currentLDFG.inputBasicVar[j]):
                            currentLDFG.inputBasicVar[i] = \
                                currentLDFG.inputBasicVar[i].merge(currentLDFG.inputBasicVar[j])
                            del currentLDFG.inputBasicVar[j]
                            i = -1
                            break
                    i += 1

                # Output vars doublons

                i = 0
                while i < len(currentLDFG.outputBasicVar):
                    for j in range(i + 1,
                                   len(currentLDFG.outputBasicVar)):
                        if currentLDFG.outputBasicVar[i].contains(currentLDFG.outputBasicVar[j]):
                            del currentLDFG.outputBasicVar[j]
                            i = -1
                            break
                        if currentLDFG.outputBasicVar[i].intersects(currentLDFG.outputBasicVar[j]):
                            currentLDFG.outputBasicVar[i] = \
                                currentLDFG.outputBasicVar[i].merge(currentLDFG.outputBasicVar[j])
                            del currentLDFG.outputBasicVar[j]
                            i = -1
                            break
                    i += 1

            for outputRegVar in \
                currentLDFG.loopInstanceList[-1].outputRegisterVar:
                currentLDFG.outputBasicVar.append(outputRegVar)

    # Remove invalid algos

    garbageCollectorLDFG()

    # 4. Collect values for I/O variables
    # 4.1 - Init the start and end time for easy research

    startTimeLDFG = dict()  # time -> LDFG
    for k in LdfgDataBase.keys():
        myLDFG = LdfgDataBase[k]

        if myLDFG.startTime not in startTimeLDFG.keys():
            startTimeLDFG[myLDFG.startTime] = set()

        startTimeLDFG[myLDFG.startTime].add(myLDFG)

    endTimeLDFG = dict()  # time -> LDFG
    for k in LdfgDataBase.keys():
        myLDFG = LdfgDataBase[k]
        if myLDFG.endTime not in endTimeLDFG.keys():
            endTimeLDFG[myLDFG.endTime] = set()

        endTimeLDFG[myLDFG.endTime].add(myLDFG)  # ref

    # 4.2 - Collect values

    LdfgIDs = set()
    currentLDFG = dict()

    time = 0
    f = open(myTraceFileName, 'r')

    for line in f:

        ins = executionTrace.lineConnector(line)
        if ins == -1:
            time += 1
            continue

        if time in startTimeLDFG.keys():

            # patch

            for myCalc in startTimeLDFG[time]:

                LdfgIDs.add(myCalc.ID)
                currentLDFG[myCalc.ID] = myCalc

                # Build the set of input bytes

                for iv in myCalc.inputBasicVar:

                    # Registers AND constants have already their values

                    if iv.registerName == '' and iv.constant == 0:
                        for c in range(0, iv.size):
                            addr = iv.startAddress + c
                            myCalc.WALFI[addr] = 'U'  # Undefined value

                # Build the set of output bytes

                for ov in myCalc.outputBasicVar:

                    # Registers have already their values

                    if ov.registerName == '':
                        for c in range(0, ov.size):
                            addr = ov.startAddress + c
                            myCalc.WALFO[addr] = 'U'  # Undefined value

        if len(LdfgIDs) != 0:
            for myLdfgID in LdfgIDs:
                count = 0
                for rAddr in ins.memoryReadAddress:
                    for indexByte in range(0,
                            ins.memoryReadSize[count]):
                        addrReadByte = int(rAddr, 16) + indexByte  # int
                        valueReadByte = \
                            (ins.memoryReadValue[count])[indexByte
                            * 2:indexByte * 2 + 2]
                        if addrReadByte \
                            in currentLDFG[myLdfgID].WALFI.keys():

                            # PATCH: we still recollect values (if *not*
                            # already written), in the hope to avoid
                            # endianness problems...

                            if currentLDFG[myLdfgID].WALFI[addrReadByte] \
                                == 'U':
                                currentLDFG[myLdfgID].WALFI[addrReadByte] = \
                                    valueReadByte
                            elif addrReadByte \
                                in currentLDFG[myLdfgID].WALFO.keys() \
                                and currentLDFG[myLdfgID].WALFO[addrReadByte] \
                                == 'U':
                                currentLDFG[myLdfgID].WALFI[addrReadByte] = \
                                    valueReadByte
                    count += 1

                count = 0
                for wAddr in ins.memoryWriteAddress:
                    for indexByte in range(0,
                            ins.memoryWriteSize[count]):
                        addrWriteByte = int(wAddr, 16) + indexByte  # int
                        valueWriteByte = \
                            (ins.memoryWriteValue[count])[indexByte
                            * 2:indexByte * 2 + 2]

                        # Different processing than for inputs: we collect all output access

                        if addrWriteByte \
                            in currentLDFG[myLdfgID].WALFO.keys():
                            currentLDFG[myLdfgID].WALFO[addrWriteByte] = \
                                valueWriteByte
                    count += 1

        if time in endTimeLDFG.keys():

            for myCalc in endTimeLDFG[time]:

                # Copy the collected values back in the input variables

                for iv in myCalc.inputBasicVar:
                    if iv.registerName == '' and iv.constant == 0:
                        for c in range(0, iv.size):

                            if myCalc.WALFI[iv.startAddress + c] == 'U':
                                print 'ERROR - A value missed ?! (r)'
                                return

                            iv.value[c] = myCalc.WALFI[iv.startAddress
                                    + c]

                # Copy the collected values back in the output variables

                for ov in myCalc.outputBasicVar:
                    if ov.registerName == '':
                        for c in range(0, ov.size):

                            if myCalc.WALFO[ov.startAddress + c] == 'U':
                                print 'ERROR - A value missed ?! (w)'
                                return

                            ov.value[c] = myCalc.WALFO[ov.startAddress
                                    + c]

                LdfgIDs.remove(myCalc.ID)

        time += 1

    f.close()
