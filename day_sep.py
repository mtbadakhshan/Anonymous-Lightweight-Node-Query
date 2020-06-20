import re

_days = {}

def day_sep(input_file):
	for _, line in enumerate(input_file):
		m = re.findall(r"#####TIME\s=\s(\d+)-(\d+)-(\d+).*\n", line)
		if (m):
			# day_out.close();
			print(m[0][0]+m[0][1]+m[0][2])
			day = m[0][0]+m[0][1]+m[0][2];
			_days[day] = True
			day_out = open('Days/Texts/'+day+'.txt','a');

		else:
			day_out.write(line)





	# data = input_file.readline();
	# begin = 0;


	# for m in re.finditer(r"#####TIME\s=\s(\d+)-(\d+)-(\d+).*\n", data):
	# 	# print(m.group(1)+m.group(2)+m.group(3), m.start(), m.end())
	# 	day = m.group(1)+m.group(2)+m.group(3)
	# 	_days[day] = True
	# 	end =  0
	# 	# with open('Days/'+day+'.txt','a') as day_out:
	# 	# 	day_out.write()
	# 	print(_days)

	# print(data,'mamad')





if __name__ == "__main__":

	for num in range(1500, 1801):
		_file_name = 'blk' + ("%05d" %num)
		print(_file_name)
		addfile_path = 'Addresses/' + _file_name + '.txt'
		with open(addfile_path,'r') as input_file:
			day_sep(input_file)

		

