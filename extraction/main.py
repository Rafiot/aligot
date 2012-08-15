#!/usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------
# Aligot project
#
# Extraction module
#
# Copyright, licence: who cares?
# ----------------------------------------------

__doc__ = \
    """
Aligot project. This module takes care of the extraction of possible crypto algorithms from an execution trace.
"""

__version__ = '1'
__versionTime__ = '08/12'
__author__ = 'j04n'

import os
import argparse
import sys
from datetime import datetime

# These are my shit!

import loops
import loopDataFlowGraph


def main():

    # # Arguments parsing

    parser = \
        argparse.ArgumentParser(description='Extraction of possible crypto algorithms\
                                        from an execution trace.'
                                )

    # Mandatory

    parser.add_argument('trace', action='store')

    # Not mandatory

    parser.add_argument('-dg', '--debug_graph', dest='debug_graph',
                        action='store_true', default=False)
    parser.add_argument('-lsd', '--loop_storage_display',
                        dest='loop_storage_display', action='store_true'
                        , default=False)
    parser.add_argument('-ap', '--all_possible_paths',
                        dest='all_possible_paths', action='store_true',
                        default=False)
    parser.add_argument('-rf', '--result_file', action='store',
                        dest='result_file', default='result.txt')
    parser.add_argument('-gn', '--graph_name', action='store',
                        dest='graph_name', default='finalGraph')
    parser.add_argument('-lf', '--log_file', action='store',
                        dest='log_file', default='')

    args = parser.parse_args()

    myTraceFileName = args.trace

    if args.log_file != '':
        sys.stdout = open(args.log_file, 'w')

    # # The real stuff begins!

    print 'Aligot extraction module'

    print 'Magic started at'
    print datetime.now()

    print 'Loop detection...',
    ls = dict()
    ls = loops.detectLoop(myTraceFileName)
    print 'Done'

    print 'Garbage collector for invalid loops...',
    before = len(ls.keys())
    loops.garbageCollector(ls)
    after = len(ls.keys())
    print 'Done (' + str(before - after) + ' loops suppressed)'

    print 'Loop I/O...',
    loops.buildLoopIORegisters(ls, myTraceFileName)
    loops.buildLoopIOMemory(ls, myTraceFileName)
    loops.buildLoopIOConstants(ls, myTraceFileName)
    print 'Done'

    if args.loop_storage_display == True:
        print 'Loop storage display...',
        loops.displayLoopStorage(ls)
        print 'Done'

    if args.debug_graph == True:
        print 'Debug graph...',
        loops.graphLoopStorage(ls, 'DebugGraph')
        print 'Done'

    print 'Garbage collector for empty loops...',
    before = len(ls.keys())
    loops.garbageCollectorEmptyLoops(ls)
    after = len(ls.keys())
    print 'Done (' + str(before - after) + ' loops suppressed)'

    print 'Loop data flow graph building...',
    if args.all_possible_paths:
        loopDataFlowGraph.buildLDFG(ls, myTraceFileName,
                                    allPossiblePaths=1)
    else:
        loopDataFlowGraph.buildLDFG(ls, myTraceFileName)
    print 'Done'

    for k in loopDataFlowGraph.LdfgDataBase.keys():  # This is nasty.
        if loopDataFlowGraph.LdfgDataBase[k].valid:
            loopDataFlowGraph.LdfgDataBase[k].display()

    print 'Dumping results...',
    loopDataFlowGraph.dumpResults(args.result_file,os.path.split(myTraceFileName)[-1])
    print 'Done'

    print 'Magic ended at'
    print datetime.now()

    print 'Producing graph...',
    loopDataFlowGraph.graphLdfgDataBase(args.graph_name)
    print 'Done'


if __name__ == '__main__':
    main()
