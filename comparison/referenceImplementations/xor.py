
#inputs as strings: hex encoding
def decrypt(key, inputtext):
	
	outputtext = ""
	for i in range(0,len(inputtext),len(key)):
		#print "." + inputtext[i:i+len(key)] + "."
		new = int(key,16) ^ int(inputtext[i:i+len(key)],16)
		outputtext = outputtext + hex(new)[2:-1]
	
	return outputtext
	
	
if __name__ == "__main__":
	decrypt("BABABABA","CAFEBABECAFEBABE")