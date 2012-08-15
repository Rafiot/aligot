# source = http://code.activestate.com/recipes/496737-python-xtea-encryption/
import struct
from ctypes import *

def xtea_encrypt(key,block,n=32,endian="!"):
    """
        Encrypt 64 bit data block using XTEA block cypher
        * key = 128 bit (16 char) 
        * block = 64 bit (8 char)
        * n = rounds (default 32)
        * endian = byte order (see 'struct' doc - default big/network) 

        >>> z = xtea_encrypt('0123456789012345','ABCDEFGH')
        >>> z.encode('hex')
        'b67c01662ff6964a'

        Only need to change byte order if sending/receiving from 
        alternative endian implementation 

        >>> z = xtea_encrypt('0123456789012345','ABCDEFGH',endian="<")
        >>> z.encode('hex')
        'ea0c3d7c1c22557f'

    """
    v0,v1 = struct.unpack(endian+"2L",block)
    k = struct.unpack(endian+"4L",key)
    sum,delta,mask = 0L,0x9e3779b9L,0xffffffffL
    for round in range(n):
        v0 = (v0 + (((v1<<4 ^ v1>>5) + v1) ^ (sum + k[sum & 3]))) & mask
        sum = (sum + delta) & mask
        v1 = (v1 + (((v0<<4 ^ v0>>5) + v0) ^ (sum + k[sum>>11 & 3]))) & mask
    return struct.pack(endian+"2L",v0,v1)

def xtea_decrypt(key,block, delta=0x9e3779b9L, n=32,endian="!"):
    """
        Decrypt 64 bit data block using XTEA block cypher
        * key = 128 bit (16 char) 
        * block = 64 bit (8 char)
        * n = rounds (default 32)
        * endian = byte order (see 'struct' doc - default big/network) 

        >>> z = 'b67c01662ff6964a'.decode('hex')
        >>> xtea_decrypt('0123456789012345',z)
        'ABCDEFGH'

        Only need to change byte order if sending/receiving from 
        alternative endian implementation 

        >>> z = 'ea0c3d7c1c22557f'.decode('hex')
        >>> xtea_decrypt('0123456789012345',z,endian="<")
        'ABCDEFGH'

    """
    v0,v1 = struct.unpack(endian+"2L",block)
    k = struct.unpack(endian+"4L",key)
    mask = 0xffffffffL
    sum = (delta * n) & mask
    for round in range(n):
        v1 = (v1 - (((v0<<4 ^ v0>>5) + v0) ^ (sum + k[sum>>11 & 3]))) & mask
        sum = (sum - delta) & mask
        v0 = (v0 - (((v1<<4 ^ v1>>5) + v1) ^ (sum + k[sum & 3]))) & mask
    return struct.pack(endian+"2L",v0,v1)
	
