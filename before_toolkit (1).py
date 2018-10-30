import pysrt
import re

path = input("the file path:")


def check_last(text):
    if (text[-1] == '.' or text[-1] == ';' or text[-1] == '?'
        or text[-1] == '!'
        or text[-1] == "'"
       ):
        return True
    else:
        return False

def get_duration(subs,initial_idx,ending_idx):
    time = subs[initial_idx].end - subs[initial_idx].start
    if ending_idx > initial_idx:
        for i in range(initial_idx+1,ending_idx+1):
            interval = subs[i].end - subs[i].start
            time += interval
    duration = float(str(time.seconds) + '.' + str(time.milliseconds))
    return duration

def check_punctuation(my_list,index,rng):
    if index <= rng:
        return None
    find = lambda x: my_list[x] == "，" \
        or my_list[x] == "：" or my_list[x] == "-" or my_list[x] == "--" or my_list[x] == ";"
    for i in range(index-rng,index+rng+1):
        if i == len(my_list):
            break
        if find(i) == True:
            return i
            break

subs = pysrt.open(path)

for i in range(len(subs)):
        subs[i].text = subs[i].text.replace('\n',' ')
idx = 0 #current index
while idx < len(subs):

    if check_last(subs[idx].text) == True:
        idx += 1
    else:
        starting_idx = idx
        while check_last(subs[idx].text) == False:
            subs[starting_idx].text = ' '.join([subs[starting_idx].text,subs[idx+1].text])
            idx += 1
        idx += 1
subs.save(path,encoding='utf-8')

print("file saved")
