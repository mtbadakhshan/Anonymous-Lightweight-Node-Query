import matplotlib.pyplot as plt
import os
import re
import json
import time
import pickle
from datetime import datetime
import redis
import struct # To convert bytes to array

MIN_CHUNK_NUMBER = -20;
MAX_CHUNK_NUMBER = 20;

def chunk_cardinal_calculator(chunk_state):
	chunks_cardinal = {}
	for addr, chunk_id in chunk_state.items():
		if chunk_id in chunks_cardinal:
			chunks_cardinal[chunk_id] += 1
		else:
			chunks_cardinal[chunk_id] = 1

	chunks_cardinal = {chunk_id:len(chunks_members[chunk_id]) for chunk_id in chunks_members.keys()}
	return chunks_cardinal


def day_state_calculator(new_day, state, beta):
	changed_chunk = 0;
	chunks_cardinal = {x:0 for x in range(-5,100)}
	for addr in new_day:
		if addr in state:
			prev_chunk = determine_chunk(state[addr])
			state[addr] = (1-beta) * state[addr] + beta * new_day[addr]
			new_chunk = determine_chunk(state[addr])	
			if (prev_chunk != new_chunk):
				changed_chunk += 1
		else:
			state[addr] = beta * new_day[addr]
			new_chunk = determine_chunk(state[addr])
		chunks_cardinal[new_chunk] += 1


	for addr in state: 
		if addr not in new_day:
			prev_chunk = determine_chunk(state[addr])
			state[addr] = (1-beta) * state[addr]
			new_chunk = determine_chunk(state[addr]);
			if (prev_chunk != new_chunk):
				changed_chunk += 1
			chunks_cardinal[new_chunk] += 1

	return state, changed_chunk, chunks_cardinal


def day_state_calculator_database(new_day, r_db, beta, day):
	# changed_chunk_matrix [previous chunk][new chunk]
	changed_chunk_matrix = {x:{y:0 for y in range(MIN_CHUNK_NUMBER, MAX_CHUNK_NUMBER)} \
	 for x in ["nonexist", *range(MIN_CHUNK_NUMBER, MAX_CHUNK_NUMBER)]}
	chunks_cardinal = {x:0 for x in range(MIN_CHUNK_NUMBER,MAX_CHUNK_NUMBER)}
	
	print("Loading from DB...")
	with r_db.pipeline() as pipe:
		for addr in new_day:
			pipe.hgetall(addr)
		prev_score_data_list = pipe.execute()

	print("%d addresses loaded from DB" %len(prev_score_data_list))

	new_addr = 0
	changed_addresses = 0
	with r_db.pipeline() as pipe:
		for addr, prev_score_data in zip(new_day, prev_score_data_list):

			new_day_datetime_object = datetime.strptime(day, '%Y%m%d')

			if(prev_score_data): #Have seen the address already
				prev_score = float(prev_score_data[b'score'].decode("utf-8"))
				last_change = prev_score_data[b'last_change'].decode("utf-8")
				last_change_datetime_object = datetime.strptime(last_change, '%Y%m%d')
				day_interval = (new_day_datetime_object - last_change_datetime_object).days

				# I am considering the situation, when the code reaches a data which is stored in the DB and it belongs to the future.
				# (do not change any thing!)
				if(day_interval<=0):
					# print("The address %s last change belongs to a date in future or just today. Nothing changes!" %addr)
					# print("Last Change: %s, Today: %s" %(last_change, day))
					continue #Try the next address!
				new_score = (1-beta) * prev_score * day_interval + beta * new_day[addr]			

			else: #See the address right now for the first time.
				prev_score = 0
				new_score = beta * new_day[addr]
				new_addr += 1	

			# raise Exception("stop")

			try:
				prev_chunk = determine_chunk(prev_score)
				new_chunk = determine_chunk(new_score)
				changed_chunk_matrix[prev_chunk][new_chunk] += 1
				chunks_cardinal[new_chunk] += 1
			except Exception as e:
				print("addr:", addr)
				print("prev_chunk: ", prev_chunk)
				print("new_score: ", new_score)
				print("new_chunk: ", new_chunk)
				print("changed_chunk_matrix: ", changed_chunk_matrix)
				raise Exception("Error")

			

			pipe.hset(addr, "score", new_score)
			pipe.hset(addr, "last_change", day)
			changed_addresses += 1
			# pipe.hmset(addr, {"score" : new_score, "last_change": day})

		print("Saving %d addresses to DB" %changed_addresses)
		pipe.execute()


	return changed_chunk_matrix, chunks_cardinal, new_addr
	


# def day_state_calculator_database(new_day, r_db, beta):
# 	changed_chunk = 0;
# 	chunks_cardinal = {x:0 for x in range(-5,100)}

# 	for addr in new_day:
# 		if r_db.exists(addr):
# 			prev_score = float(r_db.get(addr).decode("utf-8"))
# 			prev_chunk = determine_chunk(prev_score)

# 			new_score = (1-beta) * prev_score + beta * new_day[addr]
# 			r_db.set(addr, new_score)
# 			new_chunk = determine_chunk(new_score)

# 			if (prev_chunk != new_chunk):
# 				changed_chunk += 1
# 		else:
# 			new_score = beta * new_day[addr]
# 			r_db.set(addr, new_score)
# 			new_chunk = determine_chunk(new_score)

# 		chunks_cardinal[new_chunk] += 1


# 	# for addr in r_db.scan_iter("*"): 
# 	# 	if addr not in new_day:
# 	# 		prev_score = float(r_db.get(addr).decode("utf-8"))
# 	# 		prev_chunk = determine_chunk(prev_score)

# 	# 		new_score = (1-beta) * prev_score
# 	# 		r_db.set(addr, new_score)
# 	# 		new_chunk = determine_chunk(new_score);

# 	# 		if (prev_chunk != new_chunk):
# 	# 			changed_chunk += 1
# 	# 		chunks_cardinal[new_chunk] += 1

# 	return changed_chunk, chunks_cardinal



def state_calculator(JSON_PATH, beta, r_db):
	days = [x.split('.')[0] for x in os.listdir(JSON_PATH)]
	days.sort()

	#initial state
	with open(JSON_PATH+days[0]+'.json', 'r') as input_file: 
		state = json.load(input_file)

	counter = 0
	for day in days[1:]:
		with open(JSON_PATH+day+'.json', 'r') as input_file:
			new_day = json.load(input_file)

			start_time = time.time()

			# Memory
			# state, changed_chunk, chunks_cardinal = day_state_calculator(new_day, state, beta)

			# Data Base
			print("------------------------------------------------------------------------------")
			print("DATE:", day)

			changed_chunk, chunks_cardinal, new_addr = day_state_calculator_database(new_day, r_db, beta, day)

			print("--- %s : %.3f seconds , %d new addresses ---" %(day, (time.time() - start_time), new_addr))


			# # Refine (change this later)
			# del state['Return Operation']
			# del state['Other']

			# Saving the objects:
			saving_path = 'Analysis/Values/%.1f/%s' %(beta,day)
			print('[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] ' + 'Saved to \"%s'%saving_path + '.bin\"')
			with open(saving_path + '.bin', 'wb') as f:  # Python 3: open(..., 'wb')
   				pickle.dump([(time.time() - start_time), changed_chunk, chunks_cardinal, new_addr],\
   				 f, protocol = pickle.HIGHEST_PROTOCOL)
   			
			# if(counter%20==0):
			# 	with open(saving_path + '-state' + '.json', 'w') as f:  # Python 3: open(..., 'wb')
			# 		json.dump(state, f)
			# 		print('[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] ' + saving_path + '-state' + '.json - ' "State saved" )
   			
			# counter +=1;
	r_db.save()

	with open(saving_path + '-state' + '.json', 'w') as f:  # Python 3: open(..., 'wb')
		json.dump(state, f)
		print("complete save")

def day_json_generator(input_file, output_file):
	count = {}
	for _, line in enumerate(input_file):
		line = line[:-1]
		if line in count:
			count[line]+= 1
		else:
			count[line] = 1

	json.dump(count, output_file)

def json_generator(TEXT_PATH, JSON_PATH):
	days = [x.split('.')[0] for x in os.listdir(TEXT_PATH)]
	days.sort()
	for day in days:
			print(day)
			dayfile_path = TEXT_PATH+day+'.txt'
			jsonfile_path =  JSON_PATH+day+'.json'
			with open(dayfile_path,'r') as input_file, open(jsonfile_path,'w') as output_file:
				day_json_generator(input_file, output_file)


def determine_chunk(score):
	if score == 0:
		return "nonexist"

	for p in range(MIN_CHUNK_NUMBER,MAX_CHUNK_NUMBER):
		if score < 2**(p+1):
			return p

	return MAX_CHUNK_NUMBER - 1


if __name__ == "__main__":
	beta = 0.3
	TEXT_PATH = 'Days/Texts/'
	JSON_PATH = 'Days/Jsons/'
	OUT_PATH = 'Analysis/Values/%.1f/' %(beta)
	r_db = redis.Redis()


	if(True):# Generate Jsons
		json_generator(TEXT_PATH, JSON_PATH)


	if(False):# Simulate
		state_calculator(JSON_PATH, beta, r_db)

	
	days = [x.split('.')[0].split('-')[0] for x in os.listdir(OUT_PATH)]
	days = list(set(days))
	days.sort()

	from tqdm import tqdm
	times = []
	changed_chunks = []
	n_addrs = []
	for day in tqdm(days[1:]):
		opening_path = OUT_PATH + '%s' %(day) + '.bin'
		with open(opening_path, 'rb') as f:
			time, changed_chunk, chunks_cardinal, n_addr, scores = pickle.load(f)
			times.append(time)
			changed_chunks.append(changed_chunk)
			n_addrs.append(n_addr)
		if day == '20191202':
			break

	scores = sorted(scores, reverse=True)

	plt.plot(times)
	plt.ylabel('Time (s)')
	plt.xlabel('Days')
	plt.show()

	plt.plot(changed_chunks)
	plt.ylabel('Changed')
	plt.xlabel('Days')
	plt.show()

	plt.plot(n_addrs)
	plt.ylabel('N')
	plt.xlabel('Days')
	plt.show()

	plt.plot(scores, '.k')
	plt.ylabel('Score')
	plt.xlabel('Addresses')
	plt.yscale('log', basey=2)
	plt.grid(True)
	# plt.show()
	plt.savefig('plot.png')

	# opening_path = OUT_PATH + '%s' %('20190827') + '.bin'
	# with open(opening_path, 'rb') as f:
	# 		time, changed_chunk, chunks_cardinal, n_addr, scores = pickle.load(f)
	# scores = sorted(scores, reverse=True)
	# plt.plot(scores, '.k')
	# plt.ylabel('Score')
	# plt.xlabel('Addresses')
	# plt.yscale('log', basey=2)
	# plt.grid(True)
	# # plt.show()
	# plt.savefig('plot.png')


	
	# print("Analysing ...")

	# import sys
	# toolbar_width = 40
	# sys.stdout.write("[%s]" % (" "*toolbar_width))
	# sys.stdout.flush()
	# sys.stdout.write("\b" * (toolbar_width+1))
	# score_chunk = {x:[] for x in range(0,21)}
	# counter = 0
	# progress = 0
	# for addr in state:
	# 	score_chunk[determine_chunk(state[addr])].append(state[addr])
	# 	counter += 1
	# 	if (int(counter*40/n_addr)>progress):
	# 		#update_bar
	# 		sys.stdout.write("-")
	# 		sys.stdout.flush()
	# 		progress += 1

	# sys.stdout.write("]\n")

	# print("Saving ...")
	# with open('score_chunk.bin', 'wb') as f:
	# 	pickle.dump(score_chunk, f)

	# print ("Loading...")
	# with open('score_chunk.bin', 'rb') as f:
	# 	score_chunk = pickle.load(f)

	# from math import log2
	# from tqdm import tqdm
	# import sys

	# h_chunk = {}
	# for chunk_id in score_chunk:
	# 	print(chunk_id,":")
	# 	cum = sum(score_chunk[chunk_id])
	# 	p = [x/cum + sys.float_info.epsilon for x in tqdm(score_chunk[chunk_id])]
	# 	h_chunk[chunk_id] = -1 * sum([x*log2(x) for x in tqdm(p)])

	# print(h_chunk)

	# with open(OUT_PATH+'20191016', 'rb') as f:
	# 		time, changed_chunk, chunks_cardinal, n_addr = pickle.load(f)
	# 		times.append(time)
	# 		changed_chunks.append(changed_chunk)
	
	# print(n_addr)




