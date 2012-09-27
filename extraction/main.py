#!/usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------
# Aligot project
#
# Extraction module. Given an execution trace, it extracts I/O values for
# possible cryptographic algorithms.
#
# Copyright, licence: who cares?
# ----------------------------------------------

# TODO: 
# - the code that extracts constants from an instruction works only with
#   4-bytes constant. Do we need to extract more ?
# - should we merge parameters building (memory, register, constant) in order
#   to speed up the process ?

__doc__ = ''' 
Aligot project. This module takes care of the extraction
from an execution trace of I/O values for possible crypto algorithms. 
'''

__version__ = '1'
__versionTime__ = '09/12'
__author__ = 'j04n'

import os
import argparse
import sys
from datetime import datetime

# These are my shit!

import loops
import loopDataFlowGraph as LDFG


def main():

    parser = argparse.ArgumentParser(description='Extraction of possible\
    crypto algorithms from an execution trace.' )

    # Mandatory

    parser.add_argument('trace', action='store')

    # Not mandatory

    parser.add_argument('-dg', '--debug_graph', dest='debug_graph',
                        action='store_true', default=False)

    parser.add_argument('-d', '--debug_mode', dest='debug_mode',
                        action='store_true', default=False)

    parser.add_argument('-lsd', '--loop_storage_display',
                        dest='loop_storage_display', action='store_true', 
                        default=False)

    parser.add_argument('-ap', '--all_subgraphs',
                        dest='all_subgraphs', 
                        help='Each possible subgraph of the LDFG will be extracted.',
                        action='store_true',
                        default=False)

    parser.add_argument('-sil', '--single_ins_loop',
                        dest='single_ins_loop', 
                        help='Take in consideration 1-ins loop, like rep-prefixed instruction (not done by default).',
                        action='store_true',
                        default=False)
    
    parser.add_argument('-rf', '--result_file', action='store',
                        dest='result_file', default='result.txt')
    
    parser.add_argument('-gn', '--graph_name', action='store',
                        dest='graph_name', default='finalGraph')
    
    parser.add_argument('-lf', '--log_file', action='store',
                        dest='log_file', default='')

    args = parser.parse_args()

    tracePath = args.trace

    if args.log_file != '':
        sys.stdout = open(args.log_file, 'w')

    print 'Aligot extraction module'

    print 'Magic started at'
    print datetime.now()

    if args.debug_mode:
        print 'DEBUG MODE ENABLED'
        loops.debugMode = 1

    print 'Loop detection...',
    # dict: ID -> loop object
    loopStorage = loops.detectLoop(tracePath)
    print 'Done'

    print 'Garbage collector for invalid loops...',
    before = len(loopStorage.keys())
    loops.garbageCollector(loopStorage)
    after = len(loopStorage.keys())
    print 'Done (' + str(before - after) + ' loops suppressed)'

    print 'Loop I/O...',
    loops.buildLoopIORegisters(loopStorage, tracePath)
    loops.buildLoopIOMemory(loopStorage, tracePath)
    loops.buildLoopIOConstants(loopStorage, tracePath)
    print 'Done'

    if args.loop_storage_display:
        print 'Loop storage display...',
        loops.displayLoopStorage(loopStorage)
        print 'Done'

    if args.debug_graph:
        print 'Debug graph...',
        loops.pydotGraphLoopStorage(loopStorage, 'DebugGraph')
        print 'Done'

    print 'Garbage collector for useless loops (no I/O)...',
    before = len(loopStorage.keys())
    loops.garbageCollectorUselessLoops(loopStorage)
    after = len(loopStorage.keys())
    print 'Done (' + str(before - after) + ' loops suppressed)'

    print 'Loop data flow graph building...',
    # dict: ID -> LoopDataFlow (connected component of the LDFG)
    graphStorage = LDFG.build(loopStorage, 
                            allSubgraphs=args.all_subgraphs, 
                            singleInsLoop = args.single_ins_loop)
    print 'Done'

    print 'Garbage collector for invalid LDFs...',
    LDFG.garbageCollector(graphStorage)
    print 'Done'

    print 'Loop data flow I/O building...',
    LDFG.buildIO(graphStorage)
    print 'Done'

    print 'Garbage collector for useless LDFs...',
    LDFG.garbageCollectorUselessLDF(graphStorage)
    print 'Done'

    print 'Assigning values to I/O memory parameters...',
    LDFG.assignIOValues(graphStorage,tracePath)
    print 'Done'

    LDFG.display(graphStorage)

    print 'Dumping results...',
    LDFG.dumpResults(graphStorage,args.result_file,
                                os.path.split(tracePath)[-1])
    print 'Done'

    print 'Magic ended at'
    print datetime.now()

    print 'Producing graph...',
    LDFG.pydotGraph(graphStorage,args.graph_name)
    print 'Done'


if __name__ == '__main__':
    main()
