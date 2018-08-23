import pysrt
import re
def subtitle_parse(path):
    subs = pysrt.open(path)
    for i in range(len(subs)):
        subs[i].text = subs[i].text.replace('\n',' ')
    subs_new = subs
    idx = 0
    for i in subs[1:]:
        if (
        (subs_new[idx].text[0] == '(' and subs_new[idx].text[-1] == ')') 
        or subs_new[idx].text[-1] == '.'
        or subs_new[idx].text[-1] == ';'
        or subs_new[idx].text[-1] == '?'
        or subs_new[idx].text[-1] == '!'    
        or i.start.seconds - subs_new[idx].end.seconds >= 2
        or re.match(r'\W*(\w[^,. !?"]*)', i.text).groups()[0] == 'and'
        or re.match(r'\W*(\w[^,. !?"]*)', i.text).groups()[0] == 'but'
        or re.match(r'\W*(\w[^,. !?"]*)', i.text).groups()[0] == 'so'
        or re.match(r'\W*(\w[^,. !?"]*)', i.text).groups()[0] == 'or'
        ):
            idx += 1
            subs_new[idx].text = i.text
            subs_new[idx].start = i.start
            subs_new[idx].end = i.end
        else:
            subs_new[idx].text = ' '.join([subs_new[idx].text,i.text])
            subs_new[idx].end = i.end
    while len(subs_new) > idx + 1:
        del subs[idx+1] 
    subs_new.save(path,encoding='utf-8')
