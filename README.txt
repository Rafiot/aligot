-------------------------------------------------------------------------
Aligot Project: Cryptographic Function Identification in Binary Programs

-------------------------------------------------------------------------

In order to understand the tool principle, please refer to the following paper: 
www.loria.fr/~calvetjo/papers/ccs12.pdf

0. Installation

Needed external modules:
    - networkx (for graph management)
    - pydot (for graph display)

1. Manual

The project works in three steps, corresponding to three different modules in
the code. 

Given a binary program B:

    1. Trace B and obtain the execution trace T in the Aligot format (./tracer)

    2. Use the extration part of the Aligot project (./extraction) to
    build the loop data flow graphs (LDFGs) from T. The outputs of this step
    are: 
        - A result file R containing I/O values for each LDFGs
        - A graph for each LDFG (for debug purposes)

    3. Use the comparison part of the Aligot project (./comparison) on R
    to check if one of the LDFG actually behaves like a known crypto
    algorithm.

Each part of the project can be tweaked with specific parameters, see -h for
each script. 

Regarding development, a "TODO list" is in the main.py of each module.

2. Example(s)

Coming soon...