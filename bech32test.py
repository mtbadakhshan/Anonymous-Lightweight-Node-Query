import binascii
from segwit_addr import *
from hashlib import sha256
import hashlib

Pub_key = b'\x02\x79\xBE\x66\x7E\xF9\xDC\xBB\xAC\x55\xA0\x62\x95\xCE\x87\x0B\x07\x02\x9B\xFC\xDB\x2D\xCE\x28\xD9\x59\xF2\x81\x5B\x16\xF8\x17\x98'
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

h = hashlib.new('ripemd160')
h.update(sha256(Pub_key).digest())
Hash160_Pubkey = h.digest()

print(binascii.hexlify(Hash160_Pubkey))

to_int_array = [x for x in Hash160_Pubkey]
print("to_int_array:", to_int_array)
to_int_array = [int(binascii.hexlify(x),16) for x in Hash160_Pubkey]
print("to_int_array:", to_int_array)

gen_data = encode('bc',0,to_int_array)
print("gen_data:", gen_data)

hrp = 'bc'
addr = 'bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4'

a, b = decode(hrp, addr)

print("a:\t",a)
print("b:\t",b)

data = [CHARSET.find(x) for x in addr]
print("data:\t", data)
