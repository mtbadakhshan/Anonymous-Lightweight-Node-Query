import os
import random
import json
from datetime import datetime, timedelta
import pickle

def pick_random_address(ADDR_PATH):
	selected_blk_file = random.choice(os.listdir(ADDR_PATH))
	with open(ADDR_PATH+selected_blk_file,'r') as f:
		address_pool = f.readlines()
		return random.choice(address_pool)
	
def days_addr_used(client_addr, DAYS_PATH):
	days = os.listdir(DAYS_PATH)
	days.sort()
	used_days = {}
	for day in days:
		print(day)
		with open(DAYS_PATH+day, 'r') as f:
			day_state = json.load(f)
			if client_addr in day_state.keys():
				used_days[day.split('.')[0]] = day_state[client_addr]
				print(used_days)
	return used_days

def chunk_predict(date_dict, start_date, due_date, beta):
	start_date = datetime.strptime(start_date, "%Y%m%d")
	due_date = datetime.strptime(due_date, "%Y%m%d")	
	score = 0
	day_step = timedelta(days=1)
	d = start_date
	while d <= due_date:
		if(d.strftime("%Y%m%d") in date_dict):
			score = int((1-beta) * score +  beta * date_dict[d.strftime("%Y%m%d")])
			print(d.strftime("%Y%m%d"), date_dict[d.strftime("%Y%m%d")])
		else:
			score = int((1-beta) *score)
		d += day_step
	print(score)
	return score
		
if __name__ == "__main__":
	beta = 0.3
	ADDR_PATH = 'Addresses/'
	DAYS_PATH = 'Days/Jsons/'
	CLIENTS_PATH = 'Clients/'
	IS_PREPROC_ENABLE = True

	#Find wich days address used
	if(not IS_PREPROC_ENABLE):
		#Pick a random address
		client_addr = pick_random_address(ADDR_PATH)
		print("client_addr: ", client_addr) # to remove newline
		date_dict = days_addr_used(client_addr, DAYS_PATH)
		with open(CLIENTS_PATH+client_addr+'.json', 'w') as f:
			json.dump(date_dict, f)
	else:
		client_addr = 'Return Operation' + '\n'
		with open(CLIENTS_PATH+client_addr+'.json', 'r') as f:
			date_dict = json.load(f)

	# print(date_dict)
	#Predict chunk
	predicted_score = chunk_predict(date_dict, '20190627', '20190807', beta)
	print("predicted_score: ", predicted_score)

	with open('Analysis/Values/0.3/20190807-state', 'rb') as f:
		state , _ = pickle.load(f)

	print("real_score: ", state[client_addr])