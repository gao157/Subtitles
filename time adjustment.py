import subprocess
import os
from pocketsphinx import AudioFile, get_model_path, get_data_path
import re
import pysrt
from num2words import num2words
from string import punctuation
import re
import Levenshtein as L #pip install python-levenshtein

video_file_path = input("the video file path:")
srt_file_path = input("the SRT file path:")

"""
convert video to audio and return the file path
"""
def process_video(video_file):
    def strip(text, suffix): # Strip .mp4 suffix from file name
        if not text.endswith(suffix):
            return text
        return text[:len(text) - len(suffix)]

    stripped_name = strip(video_file, ".mp4")
    audio_file = stripped_name + ".wav"
    subprocess.call(["ffmpeg -i " + video_file + " -ac 1 -ar 16000 -vn " + audio_file],  shell=True)
    return audio_file

def get_duration_from_last_sentence(subs,initial_idx):
    time = subs[initial_idx].start - subs[initial_idx-1].end
    duration = float(str(time.seconds) + '.' + str(time.milliseconds))
    return duration

"""
get rid of the punctuation
"""

def no_punc(text):
    text_clean = ''.join(c for c in text if c not in punctuation)
    return text_clean

def clean(text):
    text = text.replace('\n',' ')
    text_clean = re.sub('^.*: ', '', text) #check if a person is speaking
    if text_clean == '':
        text_clean = text   #keep the name
    text_clean = ''.join(c for c in text_clean if c not in punctuation)
    return text_clean

def is_pause(text):
    if text in ('</s>','<s>','<sil>','[SPEECH]','[NOISE]'):
        return True
    else:
        return False

def time_conversion(time):
    total_sec = time/100
    hrs = int(total_sec/3600)
    mins = int((total_sec - 3600*hrs)/60)
    secs= (total_sec - 3600*hrs - 60*mins)
    milsecs = int((secs - int(secs))*1000)
    return hrs, mins, int(secs), milsecs

audiofile = process_video(video_file_path)

model_path = get_model_path()
data_path = get_data_path()

config = {
    'verbose': True,
    'audio_file': audiofile,
    'buffer_size': 2048,
    'no_search': False,
    'full_utt': False,
    'hmm': os.path.join(model_path, 'en-us'),
    'lm': os.path.join(model_path, 'en-us.lm.bin'),
    'dict': os.path.join(model_path, 'cmudict-en-us.dict')
}

audio = AudioFile(**config)
translated_subs = []
for phrase in audio:
    translated_subs.append(phrase.segments(detailed=True))


flattened = [val for sublist in translated_subs for val in sublist]
translated_subs_no_pause = []
temp_list = []
for items in flattened:
    if is_pause(items[0]) == False:
        temp_list.append(items)
    else:
        translated_subs_no_pause.append(temp_list)
        temp_list = []
translated_subs_no_pause = [items for items in translated_subs_no_pause if items != []]

phrase_list = []
for sublist in translated_subs_no_pause:
    temp_list = []
    for tuples in sublist:
        word = tuples[0]
        temp_list.append(word)
    sentence = ' '.join(temp_list)
    sentence = re.sub('[^a-zA-Z]+', ' ', sentence)
    sentence = sentence.strip()
    phrase_list.append(sentence)

subs = pysrt.open(srt_file_path)
def check_last(text):
    if (text[-1] == '.' or text[-1] == ';'or text[-1] == '?'
        or text[-1] == '!' or text[-1] == "'"
       ):
        return True
    else:
        return False

list_of_sentences = [0]

for i in range(len(subs)):
    subs[i].text = subs[i].text.replace('\n',' ')
    text = subs[i].text
    text_clean = re.sub('^.*: ', '', subs[i].text)
    if subs[i].text == '':
        text_clean = text
    subs[i].text = text_clean

idx = 0 #current index
while idx < len(subs):
    if check_last(subs[idx].text) == True:
        list_of_sentences.append(idx)
        idx += 1

    else:
        list_of_sentences.append(idx)
        starting_idx = idx
        while check_last(subs[idx].text) == False:
            subs[starting_idx].text = ' '.join([subs[starting_idx].text,subs[idx+1].text])
            idx += 1
        idx += 1

del list_of_sentences[0]

subs1 = pysrt.open(srt_file_path)

#records the current position in phrase list
idx = 0
for i in list_of_sentences:
    # no punctuation, convert numbers to words
    sub_text = ' '.join([num2words(float(word),to='year') if word.isdigit() == True and len(word) == 4
                          else num2words(float(word),to='ordinal') if word.isdigit() == True
                          else word for word in no_punc(subs[i].text).split(' ')])

    phrase_text = ''

    #possible noise, greedy search the next best line in phrase_list
    if (idx != 0 and get_duration_from_last_sentence(subs,i) > 5) or (idx == 0 and subs[idx].start.seconds > 15):
        duration = subs[0].start.seconds if idx == 0 else get_duration_from_last_sentence(subs,i)
        search_parameter = int(round(duration/3))
        ratio_list =[]
        for j in range(idx,idx+search_parameter):
            a = phrase_list[j]
            b = sub_text
            a = a.strip()
            b = b.strip()
            l = L.ratio(a,b)
            ratio_list.append(l)

        phrase_text = phrase_list[ratio_list.index(max(ratio_list))+idx]
        idx += search_parameter
        start_idx = idx - 1
    else:
        start_idx = idx

    window = 1
    max_ratio = 0.000001
    last_max_ratio = 0


    while max_ratio > last_max_ratio:
        last_max_ratio = max_ratio
        L_ratio = []

        for j in range(idx,idx+window):
            a = ' '.join([phrase_text,phrase_list[j]])
            b = sub_text[:len(a)]
            a = a.strip()
            b = b.strip()
            L_ratio.append(L.ratio(a,b))

        max_index = L_ratio.index(max(L_ratio)) + idx
        max_ratio = L.ratio(' '.join([phrase_text, phrase_list[max_index]]),sub_text)

        if max_ratio > last_max_ratio:
            phrase_text = ' '.join([phrase_text, phrase_list[max_index]])
            phrase_text = phrase_text.strip()
            idx = max_index + 1
        else:
            last_max_ratio = max_ratio
    """
    print('Sentences matching complete')
    print("the actual text:",sub_text)
    print('the phrase text is:',phrase_text)
    """

    #slicing the sentence
    end_idx = idx - 1
    temp = translated_subs_no_pause[start_idx:end_idx+1] #lines in tr
    translated_list  = [val for sublist in temp for val in sublist]  #this flattens the list
    temp_idx = 0 #this idx tracks the current position in translated_list
    try:
        for k in range(i,list_of_sentences[list_of_sentences.index(i)+1]):

            current_text = clean(subs1[k].text)

            # map the start time
            subs1[k].start.hours = time_conversion(translated_list[temp_idx][2])[0]
            subs1[k].start.minutes = time_conversion(translated_list[temp_idx][2])[1]
            subs1[k].start.seconds = time_conversion(translated_list[temp_idx][2])[2]
            subs1[k].start.milliseconds = time_conversion(translated_list[temp_idx][2])[3]

            current_phrase = ''
            ratio_prev = 0
            ratio_next = 0.001
            while ratio_prev < ratio_next or len(current_phrase) < 0.05*len(current_text):
                ratio_prev = ratio_next
                try:
                    while is_pause(translated_list[temp_idx][0]) == True:
                        temp_idx += 1
                    #print(temp_idx, translated_list[temp_idx])
                    #this gets rid of stuff like "the(2)" and keeps letter only
                    current_phrase = ' '.join((current_phrase,re.sub('[^a-zA-Z]+', '', translated_list[temp_idx][0])))
                    current_phrase = current_phrase.lstrip()
                    ratio_next = L.ratio(current_text,current_phrase)
                    temp_idx += 1
                except IndexError:
                    pass

            temp_idx = temp_idx - 1

            # map the end time
            subs1[k].end.hours = time_conversion(translated_list[temp_idx-1][3])[0]
            subs1[k].end.minutes = time_conversion(translated_list[temp_idx-1][3])[1]
            subs1[k].end.seconds = time_conversion(translated_list[temp_idx-1][3])[2]
            subs1[k].end.milliseconds = time_conversion(translated_list[temp_idx-1][3])[3]
        """
            print('current_text:',current_text)
            print('current_phrase:',current_phrase)
        print('Slicing done')
        """
    except IndexError:
        pass

subs1.save(srt_file_path,encoding='utf-8')
