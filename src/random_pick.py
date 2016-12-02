# -*- coding: utf-8 -*-

import sys
import csv
import random

if len(sys.argv) != 3:
    print("How to implement?\n")
    print("python random_pick.py input_file.csv output_file.csv\n")

record_num = input("Entire record: ")
record_num = int(record_num)
selected_num = input("Random select: ")
selected_num = int(selected_num)
random_list = random.sample(range(record_num), selected_num)
for i in range(len(random_list)):
    random_list[i] += 1
random_list.append(0)
random_list.sort()

fread = open(sys.argv[1], 'r')
fwrite = open(sys.argv[2], 'w', newline='') 
csv_writer = csv.writer(fwrite)
csv_reader = csv.reader(fread)

check = 0
random_index = 0
for row in csv_reader:
    if check == random_list[random_index]:
        random_index += 1
        csv_writer.writerow(row)    
    check += 1
    if random_index > selected_num:
        break
fread.close()
fwrite.close()
