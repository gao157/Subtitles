import pysrt
import re
import jieba

path = input("the original english file path:")
path_1 = input("the translated file path:")


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



list_of_sentences = []

subs = pysrt.open(path)
for i in range(len(subs)):
        subs[i].text = subs[i].text.replace('\n',' ')
idx = 0 #current index
while idx < len(subs):

    if check_last(subs[idx].text) == True:
        idx += 1
    else:
        starting_idx = idx
        list_of_sentences.append(idx)
        while check_last(subs[idx].text) == False:
            subs[starting_idx].text = ' '.join([subs[starting_idx].text,subs[idx+1].text])
            idx += 1
        idx += 1

subs = pysrt.open(path_1)
lines = len(subs)
for starting_idx_position in range(len(list_of_sentences)):
    starting_idx = list_of_sentences[starting_idx_position]
    try:
        ending_idx = lines if starting_idx_position == list_of_sentences[-1] else list_of_sentences[starting_idx_position+1]
    except IndexError:
        print('stopping')
    seg_list = jieba.lcut(subs[starting_idx].text)
    list_length = len(seg_list)

    #get time elapsed of each line for partition
    d={}
    total_duration = get_duration(subs,starting_idx,ending_idx)
    for i in range(starting_idx,ending_idx):
        d[i] = get_duration(subs,i,i)/total_duration

    #partition
    for i in range(starting_idx,ending_idx):
        list_length = len(seg_list)
        total_duration = sum(d.values())
        percent = d[i]/total_duration
        cutoff_idx = round(percent*list_length)
        check = check_punctuation(seg_list,cutoff_idx,2) #check punctuation within 2 words range
        if (check == None) is False:
            cutoff_idx = check
        subs[i].text = (''.join(seg_list[0:cutoff_idx+1]))
        seg_list = seg_list[cutoff_idx+1:]
        del d[i]

subs.save(path_1,encoding='utf-8')

print("file saved")
