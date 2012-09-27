/*
Aligot project
TEA example source code

Stolen from: http://en.wikipedia.org/wiki/Tiny_Encryption_Algorithm
*/


#include "stdint.h"
#include <iostream> 
using namespace std;

 
void encrypt (uint32_t* v, uint32_t* k) {
    uint32_t v0=v[0], v1=v[1], sum=0, i;           /* set up */
    uint32_t delta=0x9e3779b9;                     /* a key schedule constant */
    uint32_t k0=k[0], k1=k[1], k2=k[2], k3=k[3];   /* cache key */
    for (i=0; i < 32; i++) {                       /* basic cycle start */
        sum += delta;
        v0 += ((v1<<4) + k0) ^ (v1 + sum) ^ ((v1>>5) + k1);
        v1 += ((v0<<4) + k2) ^ (v0 + sum) ^ ((v0>>5) + k3);
    }                                              /* end cycle */
    v[0]=v0; v[1]=v1;
}
 
void decrypt (uint32_t* v, uint32_t* k) {
    uint32_t v0=v[0], v1=v[1], sum=0xC6EF3720, i;       /* set up */
    uint32_t delta=0x9e3779b9;                          /* a key schedule constant */
    uint32_t k0=k[0], k1=k[1], k2=k[2], k3=k[3];        /* cache key */
    for (i=0; i<32; i++) {                              /* basic cycle start */
        v1 -= ((v0<<4) + k2) ^ (v0 + sum) ^ ((v0>>5) + k3);
        v0 -= ((v1<<4) + k0) ^ (v1 + sum) ^ ((v1>>5) + k1);
        sum -= delta;                                   
    }                                                   /* end cycle */
    v[0]=v0; v[1]=v1;
}

// non-standard delta value and round number
void modified_decrypt(long* v, long* k)
{
    unsigned long n=16,sum,y=v[0],z=v[1],delta=0x12345678;
    sum = delta << 4;
    while(n-->0)
    {
        z-= ((y << 4) + k[2]) ^ (y+sum) ^ ((y>>5) + k[3]);
        y-= ((z<<4) + k[0]) ^ (z+sum) ^ ((z>>5) + k[1]);
        sum-=delta;
    }
    v[0]=y;
    v[1]=z;
}

int main()
{
    
    uint32_t v1[2];
    v1[0] = 0x01234567;
    v1[1] = 0x89ABCDEF;

	cout << "Input text:" << endl;
	cout << hex << v1[0];
    cout << hex << v1[1] << endl;

    uint32_t key[4];
    key[0] = 0xDEADBEE1;
    key[1] = 0xDEADBEE2;
    key[2] = 0xDEADBEE3;
    key[3] = 0xDEADBEE4;

	cout << "Key:" << endl;
	cout << hex << key[0];
	cout << hex << key[1];
	cout << hex << key[2];
	cout << hex << key[3] << endl;

    decrypt(v1, key);

	cout << "Output text:" << endl;
    cout << hex << v1[0];
    cout << hex << v1[1] << endl;

    return 0;

}