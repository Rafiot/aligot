Aligot Project: Cryptographic Function Identification in Binary Programs

The project works in three steps. Given a binary program B:

	1. Trace B and obtain the execution trace T in the Aligot format (see ./tracer)

	2. Use the extration part of the Aligot project (see ./extraction) to build the loop data flow graphs (LDFGs) from T. The outputs of this script are:
		- A result file R containing I/O values for each LDFGs. 
		- Graphs for each LDFG (debug).

	3. Use the comparison part of the Aligot project (see ./comparison) on R to check if one of the LDFG actually behaves like a known crypto algorithm.

Each part of the project can be tweaked with specific parameters, see -h for each script.