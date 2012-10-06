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
					print 'ERROR: Already seen address (heuristics.outputMemoryAdjacency())'
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

	newInputParameters[len(newInputParameters.keys())] = curP

	l = list()
	for v in newInputParameters.values():
		l.append(v.length)

	ldf.maxLengthInput = max(l)
	ldf.minLengthInput = min(l)

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
					print 'ERROR: Already seen address (heuristics.outputMemoryAdjacency())'
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

	newOutputParameters[len(newOutputParameters.keys())] = curP

	l = list()
	for v in newOutputParameters.values():
		l.append(v.length)

	ldf.maxLengthOutput = max(l)
	ldf.minLengthOutput = min(l)

	ldf.outputParameters = newOutputParameters


def blacklistedValues(ldf, c):

	'''
		Each cipher can have some blacklisted byte values. We test if
		some parameters have all theirs bytes in theses blacklists.     
	'''

	inputBl = list()
	newInputParameters = dict() # id -> parameter

	for k in ldf.inputParameters.keys():

		ip = ldf.inputParameters[k]
		
		if c.isBlacklistedValue(ip.value):
			inputBl.append(ip)
			ldf.inputParameters.pop(k)
		else:
			newInputParameters[len(newInputParameters.keys())] = ip

	outputBl = list()
	newOutputParameters = dict()

	for k in ldf.outputParameters.keys():

		op = ldf.outputParameters[k]

		if c.isBlacklistedValue(op.value):
			outputBl.append(op)
			ldf.outputParameters.pop(k)
		else:
			newOutputParameters[len(newOutputParameters.keys())] = op

	ldf.inputParameters = newInputParameters
	ldf.outputParameters = newOutputParameters

	return [inputBl,outputBl]


def filterInputRegisters(ldf):

	'''
		Remove registers from the input parameters.
	'''

	newInputParameters = dict() # id -> parameter

	for ip in ldf.inputParameters.values():
		if ip.startAddress != 'R':
			newInputParameters[len(newInputParameters.keys())] = ip

	ldf.inputParameters = newInputParameters

def filterOutputRegisters(ldf):

	'''
		Remove registers from the output parameters.
	'''

	newOutputParameters = dict() # id -> parameter

	for op in ldf.outputParameters.values():
		if op.startAddress != 'R':
			newOutputParameters[len(newOutputParameters.keys())] = op

	ldf.outputParameters = newOutputParameters