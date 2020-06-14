import binascii
from hashlib import sha256
import hashlib
import codecs
from datetime import datetime
import base58
import os
from segwit_addr import encode
import getopt, sys



_file_name = 'blk00000'
_outfile = 0;

def varint(data, pointer):
	prefix = data[0:1]
	if(prefix == b'\xfd'):
		number = data[1:3]
		next_pointer = 3 + pointer
	elif(prefix == b'\xfe'):
		number = data[1:5]
		next_pointer = 5 + pointer
	elif(prefix == b'\xff'):
		number = data[1:9]
		next_pointer = 9 + pointer
	else:
		number = prefix
		next_pointer = 1 + pointer

	return int(binascii.hexlify(number[::-1]),16), next_pointer

def script_decoder(ScriptPubKey): #Hex input
	# 
	#Pay_To_Pubkey
	if (ScriptPubKey[0:1] == b'\x41' and ScriptPubKey[-1:] == b'\xac'): # 41:65 byte is the size of public key. ac: OP_CHECKSIG
		Pubkey = ScriptPubKey[1:-1]
		# x = Pubkey[1:33]
		# y = Pubkey[33:]
		# print(len(Pubkey[1:]), binascii.hexlify(Pubkey[1:]))
		# print(len(x), "x: ", binascii.hexlify(x))
		# print(len(y), "y: ", binascii.hexlify(y), int(binascii.hexlify(y), 16)%2)
		# if (int(binascii.hexlify(y), 16)%2):
		# 	prefix = b'\x03'
		# else:
		# 	prefix = b'\x02'

		# compressed_pubkey = prefix + x;
		# # compressed_pubkey = b'\x0c4f00a8aa87f595b60b1e390f17fc64d12c1a1f505354a7eea5f2ee353e427b72\x3c\xba\x1f\x4d\x12\xd1\xce\x0b\xce\xd7\x25\x37\x37\x69\xb2\x26\x2c\x6d\xaa\x97\xbe\x6a\x05\x88\xcf\xec\x8c\xe1\xa5\xf0\xbd\x0009'
		# print("compressed_pubkey: ", binascii.hexlify(compressed_pubkey))
		h = hashlib.new('ripemd160')
		h.update(sha256(Pubkey).digest())
		Hash160_Pubkey = h.digest()
		# ripemd160(sha256(Pubkey).digest()).digest()
		checksum = sha256(sha256(b'\x00'+Hash160_Pubkey).digest()).digest()
		# print(base58.b58encode(b'\x00'+Hash160_Pubkey+checksum[0:4])) # Pubkey : 04..., 04 means uncompressed public key
		Address = base58.b58encode(b'\x00'+Hash160_Pubkey+checksum[0:4]).decode("utf-8")
		# print(Address)
		_outfile.write( Address + os.linesep)

		# raise RuntimeError('ScriptPubKey') 
	#Pay_To_Script_Hash
	elif (ScriptPubKey[0:2] == b'\xa9\x14' and ScriptPubKey[-1:] == b'\x87'): # a9:OP_HASH160, 14: 20bytes to push, 87:OP_EQUAL 
		Hash160_Script = ScriptPubKey[2:-1]
		checksum = sha256(sha256(b'\x05'+Hash160_Script).digest()).digest()
		# print(base58.b58encode(b'\x05'+Hash160_Script+checksum[0:4]))
		Address = base58.b58encode(b'\x05'+Hash160_Script+checksum[0:4]).decode("utf-8")
		# print(Address)
		_outfile.write(Address + os.linesep)
	#Pay_To_PubkeyHash
	elif (ScriptPubKey[0:3] == b'\x76\xa9\x14' and ScriptPubKey[-2:] == b'\x88\xac'): #76:OP_DUP, a9:OP_HASH160, 14: 20bytes to push, 88:OP_EQUALVERIFY, ac: OP_CHECKSIG
		Hash160_Pubkey = ScriptPubKey[3:-2]
		checksum = sha256(sha256(b'\x00'+Hash160_Pubkey).digest()).digest()
		 # print(binascii.hexlify(checksum[0:4]))
		# print(base58.b58encode(b'\x00'+Hash160_Pubkey+checksum[0:4]))
		Address = base58.b58encode(b'\x00'+Hash160_Pubkey+checksum[0:4]).decode("utf-8")
		_outfile.write(Address + os.linesep)
	elif (ScriptPubKey[0:1] == b'\x6a'):
		Data = ScriptPubKey[2:]
		# print("Return Operation")
		_outfile.write("Return Operation" + os.linesep)
	elif (ScriptPubKey[0:1] == b'\x00'): # I just handled Bech32 version 0
		# print("ScriptPubKey: ", binascii.hexlify(ScriptPubKey))
		ScriptPubKey_array = [x for x in ScriptPubKey[2:]]
		# print("ScriptPubKey_array: ", ScriptPubKey_array)
		Address = encode('bc',0,ScriptPubKey_array)
		# print("Address: ", Address)
		_outfile.write(Address + os.linesep)
		if (ScriptPubKey[1:2] != b'\x20' and ScriptPubKey[1:2] != b'\x14'):
			print(binascii.hexlify(ScriptPubKey[1:2]))
			raise Exception('Error in Bech32 detected')
	else:
		# print("other")
		_outfile.write("Other" + os.linesep)



# Block Extractor: Extract Blocks from blk.dat
def block_decomposition(blkdatafile_path):
	MAGIC_BYTE = b'\xf9\xbe\xb4\xd9'
	Blocks = {
		# "id" : {
		# 	"Version" : 
		# 	"PrevHash" :
		# 	"MerkleRoot" :
		# 	"Time" :
		# 	"Bits" :
		# 	"Nonce" :
		# 	"Transactions":
		# }
	}
	with open(blkdatafile_path, 'rb') as f:
		i = 0
		pointer = 0;
		while True:
			# print("pointer: ", pointer)
			# print(i)
			i+=1
			magic_byte = f.read(4)
			if( magic_byte != MAGIC_BYTE):
				# raise Exception('No Magic-Byte found at the beginning of the block. Magic-Byte:',
				#  binascii.hexlify(magic_byte))
				return
			block_size = int(binascii.hexlify(f.read(4)[::-1]),16)
			block = f.read(block_size)
			header = block[pointer:pointer+80]
			# blockid = binascii.hexlify(sha256(sha256(codecs.decode(binascii.hexlify(header),'hex')).digest()).digest()[::-1])
			# print(blockid)
			tx_count, new_pointer = varint(block[pointer+80:], pointer+80)

			# Blocks[blockid] = {
			# 	"Header" : {
			# 		"Version" : binascii.hexlify(header[0:4][::-1]),
			# 		"PrevHash" : binascii.hexlify(header[4:36][::-1]),
			# 		"MerkleRoot" : binascii.hexlify(header[36:68][::-1]),
			# 		"Time" : datetime.fromtimestamp(int(binascii.hexlify(header[68:72][::-1]),16)),
			# 		"Bits" : binascii.hexlify(header[72:76][::-1]),
			# 		"Nonce" : int(binascii.hexlify(header[76:][::-1]),16)
			# 	},
			# 	"TransactionCount": tx_count #int(binascii.hexlify(tx_count[::-1]),16)
			# }



			# print("#############################################")
			# print(Blocks)
			# print("pointer", pointer)

			Time = datetime.fromtimestamp(int(binascii.hexlify(header[68:72][::-1]),16));
			_outfile.write( "#####TIME = " + str(Time) + os.linesep)
			transaction_decomposition(tx_count, block[new_pointer:])
			# pointer += block_size
			# print("#############################################")
			# break
			# print(binascii.hexlifya(f.read(4)))
					
		 
# BlockDecomposition: Extract Transaction From Blocks
def transaction_decomposition(txcount, txdata):
	pointer = 0
	for tx in range(txcount):
		# print("#tx: ", tx+1)
		version = txdata[pointer:pointer+4]; pointer += 4
		# print("txversion: ", version)
		Segwit_Flag = 0
		# print("******************************(%d)" %(tx+1))
		if(txdata[pointer:pointer+1] == b'\x00'):
			#Segwit
			Segwit_Flag = int(binascii.hexlify(txdata[pointer+1:pointer+2]), 16)
			pointer += 2

		input_count, pointer = varint(txdata[pointer:], pointer)
		# print("input_count:", input_count)
		for _ in range(input_count):
			txId = binascii.hexlify(txdata[pointer:pointer+32]); pointer += 32
			Vout = binascii.hexlify(txdata[pointer:pointer+4][::-1]); pointer += 4
			ScriptSig_size, pointer = varint(txdata[pointer:], pointer)
			ScriptSig = binascii.hexlify(txdata[pointer:pointer+ScriptSig_size]); pointer += ScriptSig_size
			Sequence = binascii.hexlify(txdata[pointer:pointer+4][::-1]); pointer += 4

			# print(input_count, txId, Vout, ScriptSig_size, Sequence)

		out_count, pointer = varint(txdata[pointer:], pointer)
		# print('out_count: ', out_count)
		for _ in range(out_count):
			# print('----------')
			Value = int(binascii.hexlify(txdata[pointer:pointer+8][::-1]),16); pointer += 8
			scriptPubKey_Size , pointer = varint(txdata[pointer:], pointer)
			# ScriptPubKey = binascii.hexlify(txdata[pointer:pointer+scriptPubKey_Size]); pointer += scriptPubKey_Size
			ScriptPubKey = txdata[pointer:pointer+scriptPubKey_Size]; pointer += scriptPubKey_Size
			script_decoder(ScriptPubKey)
			# print(binascii.hexlify(ScriptPubKey))
			# print(Value, scriptPubKey_Size, ScriptPubKey)
			 
		# print(binascii.hexlify(version[::-1]),input_count, out_count,pointer)
		
		#Segwit Parser
		if(Segwit_Flag):
			for _ in range(input_count):
				num_items , pointer = varint(txdata[pointer:], pointer)
				for _ in range(num_items):
					item_length, pointer = varint(txdata[pointer:], pointer)
					pointer += item_length;

		Locktime = txdata[pointer:pointer+4]; pointer += 4;

		# return pointer

		# break
		
		


# Extract Addresses From Transactions

# Transaction Aggrigation

# Histogram of Transactions


if __name__ == "__main__":

	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:s:t:", ["input-dir=", "start=", "to="])
	except getopt.GetoptError as err:
		print(err)
		sys.exit(2)

	print("opts: ", opts)
	print("args: ", args)

	for o, a in opts:
		if o in ("-i", "--input-dir"):
			if (a[-1] == "/"):
				input_dir = a
			else:
				input_dir = a+"/"

		elif o in ("-s", "--start"):
			start_num = int(a)
		elif o in ("-t", "--to"):
			end_num = int(a)
		else:
			assert False, "unhandled option"

	for num in range(start_num, end_num  + 1):
		_file_name = 'blk' + ("%05d" %num)
		print(_file_name)
		blkdatafile_path = input_dir +_file_name+'.dat'
		with open('./Addresses/'+_file_name+'.txt', 'w') as _outfile:
			block_decomposition(blkdatafile_path)

