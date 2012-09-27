/*
Aligot project
RC4 example source code

Stolen from: http://www.skynet.ie/~caolan/pub/wvDecrypt/wvDecrypt/rc4.c
*/

#include <iostream>
#include <cstring>
#include <sstream>
#include <iomanip>
using namespace std;

#include "rc4.h"
static void swap_byte(unsigned char *a, unsigned char *b);

void prepare_key(unsigned char *key_data_ptr, int key_data_len,
		 rc4_key *key)
{
   unsigned char index1;
   unsigned char index2;
   unsigned char* state;
   short counter;     

   state = &key->state[0];         
   for(counter = 0; counter < 256; counter++)              
   state[counter] = counter;      


   key->x = 0;     
   key->y = 0;     
   index1 = 0;     
   index2 = 0;             


   for(counter = 0; counter < 256; counter++)      
   {               
      index2 = (key_data_ptr[index1] + state[counter] +
                index2) % 256;                
      swap_byte(&state[counter], &state[index2]);            
      
      index1 = (index1 + 1) % key_data_len;  
   }       
}

void rc4(unsigned char *buffer_ptr, int buffer_len, rc4_key *key)
{ 
   unsigned char x;
   unsigned char y;
   unsigned char* state;
   unsigned char xorIndex;
   short counter;              
   
   x = key->x;     
   y = key->y;     
   
   state = &key->state[0];         
   for(counter = 0; counter < buffer_len; counter ++)      
   {               
      x = (x + 1) % 256;                      
      y = (state[x] + y) % 256;               
      swap_byte(&state[x], &state[y]);                        
      
      xorIndex = (state[x] + state[y]) % 256;                 
      
      buffer_ptr[counter] ^= state[xorIndex];         
   }               
   key->x = x;     
   key->y = y;
}

static void swap_byte(unsigned char *a, unsigned char *b)
{
   unsigned char swapByte; 
   
   swapByte = *a; 
   *a = *b;      
   *b = swapByte;
}

std::string char_to_hex(const char* input)
{
    stringstream stream;
	for(int i=0; i<(int)strlen(input)/2; i++)
	{
		stream << hex << setfill('0') << setw(2) << ((int)input[i] & 0x000000FF);
	}
	string result(stream.str());
	return result;
}


int main()
{
	string key = "SuperKeyIsASuperKey";

	cout << "Key:" << endl;
	cout << key.c_str() << endl;

	string plaintext = "SuperPlainMessageABaseDeTrompette";

	cout << "Plaintext:" << endl;
	cout << plaintext.c_str() << endl;

	// Prepare the key
	rc4_key rc4Key;
	
	prepare_key((unsigned char *)key.c_str(), key.length(), &rc4Key);

	rc4((unsigned char *)plaintext.c_str(), plaintext.length(), &rc4Key);

	cout << "Encrypted text:" << endl;
	cout << char_to_hex(plaintext.c_str()) << endl;

	getchar();

	return 0;
}
