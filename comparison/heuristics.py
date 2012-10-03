
import parameter

def inputMemoryAdjacency(ldf):

	'''
		We group together input parameters that are adjacent in memory.
	'''

	newInputParameters = dict() # id -> parameter
	memoryMap = dict() # addr (int) -> value (string)

	for ip in ldf.inputParameters.values():

		# don't apply to registers|constants, we keep them as it
		if ip.startAddress == 'R' or ip.startAddress == 'C':
			newInputParameters[len(newInputParameters.keys())] = ip
		else:
			# feed the memory map
			for count in range(ip.length):
				byteAddr = int(ip.startAddress,16) + count
				if byteAddr in memoryMap.keys():
					print 'ERROR: Already seen address (heuristics.memoryAdjacency())'
					quit()
				memoryMap[byteAddr] = ip.value[count*2:(count*2)+2]

	curP = None
	for k in sorted(memoryMap.keys()):
		if curP is None:
			curP = parameter.parameter(hex(k)[2:],1,memoryMap[k])
		else:
			# is it adjacent ?
			if k == (int(curP.startAddress,16) + curP.length):
				curP.incrementSize(memoryMap[k])
			else:
				newInputParameters[len(newInputParameters.keys())] = curP
				curP = parameter.parameter(hex(k)[2:],1,memoryMap[k])

	ldf.inputParameters = newInputParameters

def outputMemoryAdjacency(ldf):

	'''
		We group together output parameters that are adjacent in memory.
	'''

	newOutputParameters = dict() # id -> parameter
	memoryMap = dict() # addr (int) -> value (string)

	for op in ldf.outputParameters.values():

		# don't apply to registers|constants, we keep them as it
		if op.startAddress == 'R' or op.startAddress == 'C':
			newOutputParameters[len(newOutputParameters.keys())] = op
		else:
			# feed the memory map
			for count in range(op.length):
				byteAddr = int(op.startAddress,16) + count
				if byteAddr in memoryMap.keys():
					print 'ERROR: Already seen address (heuristics.memoryAdjacency())'
					quit()
				memoryMap[byteAddr] = op.value[count*2:(count*2)+2]

	curP = None
	for k in sorted(memoryMap.keys()):
		if curP is None:
			curP = parameter.parameter(hex(k)[2:],1,memoryMap[k])
		else:
			# is it adjacent ?
			if k == (int(curP.startAddress,16) + curP.length):
				curP.incrementSize(memoryMap[k])
			else:
				newOutputParameters[len(newOutputParameters.keys())] = curP
				curP = parameter.parameter(hex(k)[2:],1,memoryMap[k])

	ldf.outputParameters = newOutputParameters


def blacklistedValues(ldf, c):

	'''
		Each cipher can have some blacklisted values, we test this here.
	'''

	inputBl = list()
	newInputParameters = dict() # id -> parameter

	for k in ldf.inputParameters.keys():

		ip = ldf.inputParameters[k]

		if ip.value in c.getBlacklistedValues():

			inputBl.append(ip)
			ldf.inputParameters.pop(k)

		else:
			newInputParameters[len(newInputParameters.keys())] = ip

	outputBl = list()
	newOutputParameters = dict()

	for k in ldf.outputParameters.keys():

		op = ldf.outputParameters[k]

		if op.value in c.getBlacklistedValues():

			outputBl.append(op)
			ldf.inputParameters.pop(k)

		else:
			newOutputParameters[len(newOutputParameters.keys())] = op

	# sinon, test pour chaque param de chacun de ses bytes

	ldf.inputParameters = newInputParameters
	ldf.outputParameters = newOutputParameters

	return [inputBl,outputBl]