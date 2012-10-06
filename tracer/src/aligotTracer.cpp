// Aligot projet
// Pintool to collect full execution traces (with data accesses)
// 
// Author: j04n

#include "pin.H"
extern "C" {
#include "xed-interface.h"
}

#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <set>
#include <map>

using namespace std;

ofstream* traceFile = 0;
int startAddress = 0x0;
bool tracingStarted = true; // default mode

int endAddress = 0x0;
bool endAddressToTest = false; // default mode
bool traceFinish = false;
bool thisIsTheEnd = false;
bool firstInstruction = true;

VOID * recordWriteAddress = 0;
INT32 recordWriteSize = 0;

void dumpRegister(int registerDef, CONTEXT * ctx);

int countStaticInstructions = 0;
map<int,string> staticInstructions;

// Output format
int binaryRepresentation = 0; // by default instructions are displayed in assembly form
int displayFlags = 0; // by default flags are not printed

// Trick to avoid playing with new strings everytime we see an API call
map<string,int> apiFunctionsStr2Int;
map<int,string> apiFunctionsInt2Str;
int countApiFunctions = 0;
int w8ForReturnAddr = 0;


// type can be :
//  0 : first call for the instruction : put an \n plus the @ and assembly code
//  1 : read memory : @ of the read + size + the actual value
//  2 : write memory : @ of the write + size + the actual value
//  3 : read register : register name + actual value
//  4 : write register : register name + actual value
VOID Analysis(int type, 
			  ADDRINT pc,
			  int disasIndex,
			  ADDRINT memAddress, 
			  int memSize, 
			  int registersUsed,
			  CONTEXT * ctx)
{

	if(thisIsTheEnd && (pc != endAddress))
		return;

	// End it at the.. end address
	// We do the test here because only the analysis function corresponds the actual execution of the end address
	if(endAddressToTest && (pc == endAddress))
	{
		// Oh really ? we have to wait until the analysis function terminates
		// Safe way : just do nothin man !
		thisIsTheEnd = true;
	}

	if(w8ForReturnAddr != 0)
	{
		if((int)pc == w8ForReturnAddr)
			w8ForReturnAddr = 0;
		else
			return;
	}

	int value = 0;
	switch(type)
	{
		case 0: // initial call
			
			if(firstInstruction)
			{
				firstInstruction = false;
				*traceFile << "!SOT" << endl;
				*traceFile << hex << pc << "!" << staticInstructions[disasIndex];
			}
			else
				*traceFile << "\n" << hex << pc << "!" << staticInstructions[disasIndex];

			// If we do that, it bugs ;/
			// Has Pin a kind of garbage collector that frees the pointers passed as arguments ?
			// (We don,t free the context either)
			//free(disas); 

			break;

		case 1: // read memory
			
			*traceFile << "!RM_" << hex << memAddress << "_" << memSize << "_";

			// Strange bug here on some binaries, a direct call to PIN_SafeCopy(&value, (void*)memAddress, memSize) will fail
			// (stupid) patch:
			switch(memSize)
			{
				case 1:
					PIN_SafeCopy(&value, (void*)memAddress, 1);
					break;
				case 2:
					PIN_SafeCopy(&value, (void*)memAddress, 2);
					break;
				case 4:
					PIN_SafeCopy(&value, (void*)memAddress, 4);
					break;
			}
			*traceFile << hex << value;
			break;

		case 2: // write memory
			
			*traceFile << "!WM_" << hex << memAddress << "_" << memSize << "_";
			
			// Strange bug here on some binaries, a direct call to PIN_SafeCopy(&value, (void*)memAddress, memSize) will fail
			// (stupid) patch:
			switch(memSize)
			{
				case 1:
					PIN_SafeCopy(&value, (void*)memAddress, 1);
					break;
				case 2:
					PIN_SafeCopy(&value, (void*)memAddress, 2);
					break;
				case 4:
					PIN_SafeCopy(&value, (void*)memAddress, 4);
					break;
			}
			*traceFile << hex << value;
			break;

		case 3: // read register
			
			*traceFile << "!RR";
			dumpRegister(registersUsed, ctx);
			break;

		case 4: // write register
			
			*traceFile << "!WR";
			dumpRegister(registersUsed, ctx);
			
			break;

		default:
			*traceFile << "Unknown type!" << endl;
			break;

	}
	
}

static VOID RecordWriteAddrSize(VOID * addr, INT32 size)
{
    recordWriteAddress = addr;
    recordWriteSize = size;
}

static VOID RecordMemWrite(ADDRINT ip)
{
    Analysis(2,
		ip,
		NULL,
		(ADDRINT)recordWriteAddress,
		recordWriteSize,
		0,
		NULL);
}

/*! dumpRegister
 * @param[in]   registerDef   Registers flags
 */
void dumpRegister(int registerDef, CONTEXT * ctx)
{

	int value = 0;
	if(registerDef & 0x00000001)
	{
		value = PIN_GetContextReg(ctx, REG_EAX);
		*traceFile << "_eax_" << hex << value;
	}
	if(registerDef & 0x00000002)
	{
		value = PIN_GetContextReg(ctx, REG_EAX);
		value = value & 0x0000FFFF;
		*traceFile << "_ax_" << hex << value;
	}
	if(registerDef & 0x00000004)
	{
		value = PIN_GetContextReg(ctx, REG_EAX);
		value = (value & 0x0000FF00) >> 8;
		*traceFile << "_ah_" << hex << value;
	}
	if(registerDef & 0x00000008)
	{
		value = PIN_GetContextReg(ctx, REG_EAX);
		value = value & 0x000000FF;
		*traceFile << "_al_" << hex << value;
	}
	if(registerDef & 0x00000010)
	{
		value = PIN_GetContextReg(ctx, REG_EBX);
		*traceFile << "_ebx_" << hex << value;
	}
	if(registerDef & 0x00000020)
	{
		value = PIN_GetContextReg(ctx, REG_EBX);
		value = value & 0x0000FFFF;
		*traceFile << "_bx_" << hex << value;
	}
	if(registerDef & 0x00000040)
	{
		value = PIN_GetContextReg(ctx, REG_EBX);
		value = (value & 0x0000FF00) >> 8;
		*traceFile << "_bh_" << hex << value;
	}
	if(registerDef & 0x00000080)
	{
		value = PIN_GetContextReg(ctx, REG_EBX);
		value = value & 0x000000FF;
		*traceFile << "_bl_" << hex << value;
	}
	if(registerDef & 0x00000100)
	{
		value = PIN_GetContextReg(ctx, REG_ECX);
		*traceFile << "_ecx_" << hex << value;
	}
	if(registerDef & 0x00000200)
	{
		value = PIN_GetContextReg(ctx, REG_ECX);
		value = value & 0x0000FFFF;
		*traceFile << "_cx_" << hex << value;
	}
	if(registerDef & 0x00000400)
	{
		value = PIN_GetContextReg(ctx, REG_ECX);
		value = (value & 0x0000FF00) >> 8;
		*traceFile << "_ch_" << hex << value;
	}
	if(registerDef & 0x00000800)
	{
		value = PIN_GetContextReg(ctx, REG_ECX);
		value = value & 0x000000FF;
		*traceFile << "_cl_" << hex << value;
	}
	if(registerDef & 0x00001000)
	{
		value = PIN_GetContextReg(ctx, REG_EDX);
		*traceFile << "_edx_" << hex << value;
	}
	if(registerDef & 0x00002000)
	{
		value = PIN_GetContextReg(ctx, REG_EDX);
		value = value & 0x0000FFFF;
		*traceFile << "_dx_" << hex << value;
	}
	if(registerDef & 0x00004000)
	{
		value = PIN_GetContextReg(ctx, REG_EDX);
		value = (value & 0x0000FF00) >> 8;
		*traceFile << "_dh_" << hex << value;
	}
	if(registerDef & 0x00008000)
	{
		value = PIN_GetContextReg(ctx, REG_EDX);
		value = value & 0x000000FF;
		*traceFile << "_dl_" << hex << value;
	}
	if(registerDef & 0x00010000)
	{
		value = PIN_GetContextReg(ctx, REG_EBP);
		*traceFile << "_ebp_" << hex << value;
	}
	if(registerDef & 0x00020000)
	{
		value = PIN_GetContextReg(ctx, REG_ESP);
		*traceFile << "_esp_" << hex << value;
	}
	if(registerDef & 0x00040000)
	{
		value = PIN_GetContextReg(ctx, REG_ESI);
		*traceFile << "_esi_" << hex << value;
	}
	if(registerDef & 0x00080000)
	{
		value = PIN_GetContextReg(ctx, REG_EDI);
		*traceFile << "_edi_" << hex << value;
	}

}

/*! addRegister
 * @param[in]   registerDef   register flags
 * @param[in]   registerName  register to add
 * @rv						  new register flags
 */
int addRegister(int registerDef, string registerName)
{
	int newRegisterDef = registerDef;

	if(registerName.compare(string("eax"))==0)
		newRegisterDef |= 0x00000001;
	else if(registerName.compare(string("ax"))==0)
		newRegisterDef |= 0x00000002;
	else if(registerName.compare(string("ah"))==0)
		newRegisterDef |= 0x00000004;
	else if(registerName.compare(string("al"))==0)
		newRegisterDef |= 0x00000008;
	else if(registerName.compare(string("ebx"))==0)
		newRegisterDef |= 0x00000010;
	else if(registerName.compare(string("bx"))==0)
		newRegisterDef |= 0x00000020;
	else if(registerName.compare(string("bh"))==0)
		newRegisterDef |= 0x00000040;
	else if(registerName.compare(string("bl"))==0)
		newRegisterDef |= 0x00000080;
	else if(registerName.compare(string("ecx"))==0)
		newRegisterDef |= 0x00000100;
	else if(registerName.compare(string("cx"))==0)
		newRegisterDef |= 0x00000200;
	else if(registerName.compare(string("ch"))==0)
		newRegisterDef |= 0x00000400;
	else if(registerName.compare(string("cl"))==0)
		newRegisterDef |= 0x00000800;
	else if(registerName.compare(string("edx"))==0)
		newRegisterDef |= 0x00001000;
	else if(registerName.compare(string("dx"))==0)
		newRegisterDef |= 0x00002000;
	else if(registerName.compare(string("dh"))==0)
		newRegisterDef |= 0x00004000;
	else if(registerName.compare(string("dl"))==0)
		newRegisterDef |= 0x00008000;
	else if(registerName.compare(string("ebp"))==0)
		newRegisterDef |= 0x00010000;
	else if(registerName.compare(string("esp"))==0)
		newRegisterDef |= 0x00020000;
	else if(registerName.compare(string("esi"))==0)
		newRegisterDef |= 0x00040000;
	else if(registerName.compare(string("edi"))==0)
		newRegisterDef |= 0x00080000;

	return newRegisterDef;

}

string addFlags(string originalString, int readFlags, int writtenFlags)
{

	int flags[] = {readFlags, writtenFlags};
	int i;
	
	string newString = originalString;

	for(i=0;i<2;i++)
	{
		if(flags[i] != 0x0)
		{
			if(i==0)
				newString.append("!RF");
			else
				newString.append("!WF");

			if(flags[i] & 0x0001)
				newString.append("_CF");
			if(flags[i] & 0x0004)
				newString.append("_PF");
			if(flags[i] & 0x0010)
				newString.append("_AF");
			if(flags[i] & 0x0040)
				newString.append("_ZF");
			if(flags[i] & 0x0080)
				newString.append("_SF");
			if(flags[i] & 0x0100)
				newString.append("_TF");
			if(flags[i] & 0x0200)
				newString.append("_IF");
			if(flags[i] & 0x0400)
				newString.append("_DF");
			if(flags[i] & 0x0800)
				newString.append("_OF");

		}
	}

	return newString;
}


VOID Fini(INT32 code, VOID *v)
{
	*traceFile << "\n!EOT" << endl;
}

// Pin calls this function every time a new instruction is encountered
VOID Instrumentation(INS ins, VOID *v)
{
	if(w8ForReturnAddr != 0)
	{
		if((int)INS_Address(ins) == w8ForReturnAddr)
			w8ForReturnAddr = 0;
		else
			return;
	}

	// Start the tracing at the.. start address
	// The end address will be tested in the analysis function
	if(!tracingStarted && ((int)INS_Address(ins) == startAddress))
		tracingStarted = true;
	if(!tracingStarted)
		return;

	int readFlags = 0x0;
	int writtenFlags = 0x0;

	if(displayFlags)
	{
		static const xed_state_t dstate = { XED_MACHINE_MODE_LEGACY_32, XED_ADDRESS_WIDTH_32b}; // 32 bits !

		xed_decoded_inst_t xedd; 
		xed_decoded_inst_zero_set_mode(&xedd,&dstate);

		xed_error_enum_t xed_code = xed_decode(&xedd, reinterpret_cast<UINT8*>(INS_Address(ins)), 15);
		BOOL xed_ok = (xed_code == XED_ERROR_NONE);	

		if (xed_ok) {	

			xed_encoder_request_init_from_decode(&xedd);

			if (xed_decoded_inst_uses_rflags(&xedd)) 
			{
				const xed_simple_flag_t* rfi = xed_decoded_inst_get_rflags_info(&xedd);
				
				if (xed_simple_flag_reads_flags(rfi)) 
				{
					const xed_flag_set_t* read_set = xed_simple_flag_get_read_flag_set(rfi);
					readFlags = xed_flag_set_mask(read_set);
				}
				else if (xed_simple_flag_writes_flags(rfi)) 
				{
					const xed_flag_set_t* written_set = xed_simple_flag_get_written_flag_set(rfi);
					writtenFlags = xed_flag_set_mask(written_set);
				}
			}
		}
	}

	// An instruction is instrumented one time for each effect : mem read, mem write, reg read, reg write, plus one time for the initialization

	if(binaryRepresentation == 0)
	{
		// Lazy : we could check for doublons, but remember... it's a simple tracer for *small* programs
		if(displayFlags)
		{
			staticInstructions[countStaticInstructions]=addFlags(INS_Disassemble(ins),readFlags,writtenFlags);
		}
		else
		{
			staticInstructions[countStaticInstructions]=INS_Disassemble(ins);
		}
		
	}
	else
	{
		char buff[16];
		memset(buff,'\x0',16);

		PIN_SafeCopy(buff,(void *)INS_Address(ins),INS_Size(ins));
		
		stringstream stream;
		for(int i=0; i<(int)INS_Size(ins); i++)
		{
			stream << hex << setfill('0') << setw(2) << ((int)buff[i] & 0x000000FF);
		}
		string binaryCode(stream.str());
	
		// Lazy : we could check for doublons, but remember... it's a simple tracer for *small* programs
		if(displayFlags)
		{
			staticInstructions[countStaticInstructions]=addFlags(binaryCode,readFlags,writtenFlags);
		}
		else
		{
			staticInstructions[countStaticInstructions]=binaryCode;
		}
	}
	
	INS_InsertCall(ins,
					IPOINT_BEFORE,
					(AFUNPTR)Analysis,
					IARG_UINT32,0,
					IARG_INST_PTR,
					IARG_UINT32,countStaticInstructions,
					IARG_END);

	countStaticInstructions++;

	// Memory reads
	if (INS_IsMemoryRead(ins)) // Deal also with the natural reads (POP & RET on the stack)
	{

		INS_InsertCall(ins,
					IPOINT_BEFORE,
					(AFUNPTR)Analysis,
					IARG_UINT32,1,
					IARG_INST_PTR,
					IARG_UINT32,0,
					IARG_MEMORYREAD_EA,
					IARG_UINT32,INS_MemoryReadSize(ins),
					IARG_UINT32,0,
					IARG_CONTEXT,
					IARG_END);
	}
	if(INS_HasMemoryRead2(ins)) // e.g. "CMPS" instruction
			INS_InsertCall(ins,
					IPOINT_BEFORE,
					(AFUNPTR)Analysis,
					IARG_UINT32,1,
					IARG_INST_PTR,
					IARG_UINT32,0,
					IARG_MEMORYREAD2_EA,
					IARG_UINT32,INS_MemoryReadSize(ins),
					IARG_UINT32,0,
					IARG_CONTEXT,
					IARG_END);
	
	// Memory writes
	if(INS_IsMemoryWrite(ins)) // Deal with the natural writes (PUSH & CALL on the stack)
	{

		INS_InsertCall(
            ins, IPOINT_BEFORE, (AFUNPTR)RecordWriteAddrSize,
            IARG_MEMORYWRITE_EA,
            IARG_MEMORYWRITE_SIZE,
            IARG_END);
        
        if (INS_HasFallThrough(ins))
        {
            INS_InsertCall(
                ins, IPOINT_AFTER, (AFUNPTR)RecordMemWrite,
                IARG_INST_PTR,
                IARG_END);
        }
        if (INS_IsBranchOrCall(ins)) //else ?
        {
            INS_InsertCall(
                ins, IPOINT_TAKEN_BRANCH, (AFUNPTR)RecordMemWrite,
                IARG_INST_PTR,
                IARG_END);
        }
	}

	int registersRead = 0x0;
	int registersWrite = 0x0;

	// Register reads
	REG readReg = INS_RegR(ins,0);
	if(REG_valid(readReg))
	{
		int k = 0;
		while (REG_valid(readReg))
		{
			registersRead=addRegister(registersRead,REG_StringShort(readReg));
			k=k+1;
			readReg = INS_RegR(ins,k);
		}

		if(registersRead != 0x0) // We only deal with GPRs + ebp/esp
		{
			
				INS_InsertCall(ins,
					IPOINT_BEFORE,
					(AFUNPTR)Analysis,
					IARG_UINT32,3,
					IARG_INST_PTR,
					IARG_UINT32,0,
					IARG_UINT32,0,
					IARG_UINT32,0,
					IARG_UINT32,registersRead,
					IARG_CONTEXT,
					IARG_END);
		}
	}
	// Register writes
	REG writeReg = INS_RegW(ins,0);
	if(REG_valid(writeReg))
	{
		
		int k = 0;
		while (REG_valid(writeReg))
		{
			registersWrite=addRegister(registersWrite,REG_StringShort(writeReg));
			k=k+1;
			writeReg = INS_RegW(ins,k);
		}

		if(registersWrite!= 0x0) // We only deal with GPRs + ebp/esp
		{
			
			// To get the written values, we have to wait after the instruction
			if (INS_HasFallThrough(ins))
			{
				INS_InsertCall(
					ins, IPOINT_AFTER, 
						(AFUNPTR)Analysis,
						IARG_UINT32,4,
						IARG_INST_PTR,
						IARG_UINT32,0,
						IARG_UINT32,0,
						IARG_UINT32,0,
						IARG_UINT32,registersWrite,
						IARG_CONTEXT,
						IARG_END);
			}
			if (INS_IsBranchOrCall(ins))
			{
				INS_InsertCall(
					ins, IPOINT_TAKEN_BRANCH, 
						(AFUNPTR)Analysis,
						IARG_UINT32,4,
						IARG_INST_PTR,
						IARG_UINT32,0,
						IARG_UINT32,0,
						IARG_UINT32,0,
						IARG_UINT32,registersWrite,
						IARG_CONTEXT,
						IARG_END);
			}

		}
	}
	
}

VOID recordApiCallEntry(int apiNumber, int returnAddr)
{
	if(!tracingStarted || thisIsTheEnd)
		return;

	if(w8ForReturnAddr != 0)
		return;

	*traceFile << "\nAPI CALL " << apiFunctionsInt2Str[apiNumber];
	w8ForReturnAddr = returnAddr;
}

VOID recordException(void)
{
	*traceFile << "\nAPI CALL: EXCEPTION!";
}



VOID imgInstrumentation(IMG img, VOID * val)
{

	if(!IMG_IsMainExecutable(img))
	{

		for( SEC sec= IMG_SecHead(img); SEC_Valid(sec); sec = SEC_Next(sec) )
		{
			// Forward pass over all routines in a section
			for( RTN rtn= SEC_RtnHead(sec); RTN_Valid(rtn); rtn = RTN_Next(rtn) )
			{
				string nameAPI = RTN_Name(rtn);
				int apiNumber = 0x1337;

				if(nameAPI == "KiUserExceptionDispatcher")
				{
					RTN_Open(rtn);
					RTN_InsertCall(rtn,
									IPOINT_BEFORE, (AFUNPTR)recordException,
									IARG_END);
					RTN_Close(rtn);
				}
				else
				{
					if((nameAPI != ".text") && (nameAPI != "unnamedImageEntryPoint"))
					{

						map<string,int>::iterator it = apiFunctionsStr2Int.find(nameAPI);
						if (it != apiFunctionsStr2Int.end())
						{
							apiNumber = it->second;
						}
						else
						{
							apiFunctionsStr2Int[nameAPI] = countApiFunctions;
							apiFunctionsInt2Str[countApiFunctions] = nameAPI;
							apiNumber = countApiFunctions;
							countApiFunctions++;
						}

						RTN_Open(rtn);
						RTN_InsertCall(rtn,
									IPOINT_BEFORE, (AFUNPTR)recordApiCallEntry,
									IARG_UINT32,apiNumber,
									IARG_RETURN_IP,
									IARG_END);
						RTN_Close(rtn);
					}
				}
			}
		}
	}
}

void displayHelpMessage()
{
	cout << "The correct command line to use this pintools is\n" << endl;
	cout << "pin -t MyTracer.dll [startA DEADBEEF] [endA DEADBEEF] [noAPIs] [binRep] [flags] -- MyExe.exe arguments" << endl;
	cout << "noAPIs : do not follow API calls" << endl;
	cout << "binRep : instructions are outputed in their executable form (hex)" << endl;
	cout << "flags : display Written Flags, and Read Flags" << endl;
}

int main(int argc, char * argv[])
{
	
	// Init
	traceFile = new ofstream("trace.out");

	// Argument parsing
	int jumpOverApisCall = 0; // default mode

	for(int i = 0; i < argc; i++) 
	{    
		
		if(strcmp(argv[i],"startA") == 0)
		{
			if((i != (argc-1)) && (isdigit(argv[i+1][0])))
			{
				sscanf_s(argv[i+1], "%x", &startAddress);
				tracingStarted = false;
			}
			else{
				cout << "Error when parsing arguments" << endl;
				displayHelpMessage();
				return 1;
			}
			
		}
		else if(strcmp(argv[i],"endA") == 0)
		{
			if((i != (argc-1)) && (isdigit(argv[i+1][0])))
			{
				sscanf_s(argv[i+1], "%x", &endAddress);
				endAddressToTest = true;
			}
			else{
				cout << "Error when parsing arguments" << endl;
				displayHelpMessage();
				return 1;
			}
		}
		else if(strcmp(argv[i],"noAPIs") == 0)
		{
			jumpOverApisCall = 1;
		}
		else if(strcmp(argv[i],"binRep") == 0)
		{
			binaryRepresentation = 1;
		}
		else if(strcmp(argv[i],"flags") == 0)
		{
			displayFlags = 1;
		}

	}

	PIN_Init(argc,argv);
	PIN_InitSymbols();
	PIN_AddFiniFunction(Fini, 0);

	if (jumpOverApisCall)
	{
		IMG_AddInstrumentFunction(imgInstrumentation,0);
	}

	INS_AddInstrumentFunction(Instrumentation, 0);
	
	// never returns
	PIN_StartProgram();
    
   return 0;
}


