import pandas as pd
import sys
import datetime
from pymystem3 import Mystem
import csv

digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
punctuation = ['.', ',', '/', '+', '\\', '-', '«', '(', ')', ':', ';', '«', '»',\
    '<', '>', '–', '"', '°', '@', '$', '%', '=', '№', '&', '_', '^', '#',\
    '?', '*', '[', ']', '{', '}', '—', '•', '\xad', '→', '|', '“', '~', '›',\
    '±', '§', '„', '…', '·', '!', '”', '’', '\x96', '‹', '‘']

def tsplit(string, delimiters):
    """Behaves str.split but supports multiple delimiters."""
    delimiters = tuple(delimiters)
    stack = [string,]
    for delimiter in delimiters:
        for i, substring in enumerate(stack):
            substack = substring.split(delimiter)
            stack.pop(i)
            for j, _substring in enumerate(substack):
                stack.insert(i+j, _substring)
    return stack

def load_dict(dict_file = "freqrnc2011.csv"):
    "Создаем словарь :) (dict) из словаря"
    df = pd.read_csv(dict_file, sep='\t', header=0, index_col=None)
    freq_dict = {}
    for lemma, freq, pos in zip(df['Lemma'].apply(lambda x: x.lower()), df['Freq(ipm)'], df['PoS']):
        freq_dict[lemma] = (freq, pos)
    return freq_dict

def load_ngrams_dict(N):
    dict_files = [0, '1grams-3.txt',\
        '2grams-3.txt',\
        '3grams-3.txt',\
        '4grams-2.txt',\
        '5grams-2.txt']
    ngrams_freq_dict = [0, {}, {}, {}, {}, {}]
    for n in range(1, N+1):
        f = open(dict_files[n], 'r')
        for line in f:
            s = str(line).lower()
            for c in punctuation:
                if c in s:
                    s = s.replace(c, '')
            w = s.split()
            if len(w) != n+1:
                continue
            s = ''
            for v in w[1:]:
                s += v + ' '
            w = (w[0], s[:-1])
            if w[1] in ngrams_freq_dict[n]:
                ngrams_freq_dict[n][w[1]] += w[0]
            else:
                ngrams_freq_dict[n][w[1]] = w[0]
        f.close()
    return(ngrams_freq_dict)

def freq_jarg_stats(scrap_file, freq_file, ngram_file, jargon_file, stats_file):
    freq_dict = load_dict()

    df = pd.read_csv(scrap_file, sep=',', header=0, index_col=None, usecols=['author'])

    # Get the number of unique authors
    authors_dict = {}
    for author in df['author']:
        if author not in authors_dict:
            authors_dict[author] = 1
    author_count = len(authors_dict)

    df = pd.read_csv(scrap_file, sep=',', header=0, index_col=None, usecols=['timestamp','text'])
    with open(jargon_file, 'w') as f_jarg:
        writer = csv.writer(f_jarg)
        writer.writerow(['timestamp','date','text','lemma','context'])
        lemmas_dict = {}
        ngrams_dict = [{} for i in ngram_file]
        mystem = Mystem()
        message_count = len(df['text'])
        lemma_count = 0
        ngrams_count = [0 for i in ngrams_dict]
        for timestamp, text in zip(df['timestamp'], df['text']):
            # Разбиваем текст сообщения на предложения
            context_ind = 0
            str_text = str(text)
            #sentences = tsplit(str_text, ['.', '?', '!'])
            sentences = [str_text]
            for sentence in sentences:
                cur_ngrams = [[] for i in ngrams_count]
                sent_analysis = mystem.analyze(sentence)
                for a in sent_analysis:
                    # Если токен не подвергается морфологическому разбору, пропускаем его
                    if ('analysis' not in a) \
                        and (a['text'][0] not in ['0','1','2','3','4','5','6','7','8','9']):
                        continue
                    # Подсчитываем количество лемм
                    cur_ngrams[1].append(a['text'].lower())
                    if (a['text'][0] in digits):
                        continue
                    lemma_count += 1
                    lemma = a['text']
                    if (len(a['analysis'])>0) and (len(a['analysis'][0])>0) and ('lex' in a['analysis'][0]):
                        lemma = a['analysis'][0]['lex']
                    if lemma in lemmas_dict:
                        lemmas_dict[lemma] += 1
                    else:
                        lemmas_dict[lemma] = 1
                    # Если токена нет в частотном словаре, включаем его в список потеницальных жаргонизмов:
                    if (len(a['analysis'])==0) or (a['analysis'][0]['lex'] in freq_dict):
                        continue
                    # Ищем контекст, в котором находится анализируемая словоформа
                    context_ind = text.find(a['text'], context_ind+1)
                    context = str_text[max(0,context_ind-85):min(len(text),context_ind+95)]
                    # Записываем в строчку все данные о необычной словоформе
                    writer.writerow([str(timestamp),
                        datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'),
                        a['text'], a['analysis'][0]['lex'], context])
                    
                # Формируем 2-, 3- и т.д. -граммы на основе 1-грамм
                for n in range(1, len(cur_ngrams)):
                    for v, w in zip(cur_ngrams[n-1][:-1], cur_ngrams[1][n-1:]):
                        cur_ngrams[n].append(v + ' ' + w)
                # Подсчитываем количество n-грам
                for n in range(1, len(ngrams_dict)):
                    for ngram in cur_ngrams[n]:
                        ngrams_count[n] += 1
                        if ngram in ngrams_dict[n]:
                            ngrams_dict[n][ngram] += 1
                        else:
                            ngrams_dict[n][ngram] = 1


    words_list = []
    for lemma, count in lemmas_dict.items():
        words_list.append((count,lemma))
    words_list.sort(reverse=True)

    with open(freq_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['lemma','pos','pos_dict','count','ipm','ipm_from_dict','ipm_ratio'])
        for w in words_list:
            ipm = w[0]*1000000./lemma_count
            ipm_from_dict = 0.
            ipm_ratio = 0.
            pos_dict = 'NA'
            if w[1] in freq_dict:
                ipm_from_dict = freq_dict[w[1]][0]
                pos_dict = freq_dict[w[1]][1]
            pos = mystem.analyze(w[1])
            if (len(pos)>0) and ('analysis' in pos[0]) and (len(pos[0]['analysis'])>0)\
            and ('gr' in pos[0]['analysis'][0]):
                pos = pos[0]['analysis'][0]['gr']
            else:
                pos = 'NA'
            if ipm_from_dict > 0:
                ipm_ratio = ipm/ipm_from_dict
            writer.writerow([w[1], pos, pos_dict, str(w[0]),
                str(round(ipm, 3)), str(round(ipm_from_dict, 3)),
                str(round(ipm_ratio, 3))])

    # Min and max timestamp
    df = pd.read_csv(scrap_file, sep=',', header=0, index_col=None, usecols=['timestamp'])
    df = list(df['timestamp'])
    first = datetime.datetime.fromtimestamp(min(df)).strftime('%Y-%m-%d')
    last = datetime.datetime.fromtimestamp(max(df)).strftime('%Y-%m-%d')

    with open(stats_file, 'w') as f:
        f.write('authors,messages,lemmas')
        for n in range(1, len(ngram_file)):
            f.write(','+str(n)+'grams')
        f.write(',first,last\n')
        f.write(str(author_count)+','+str(message_count)+','+str(lemma_count))
        for n in range(1, len(ngram_file)):
            f.write(','+str(ngrams_count[n]))
        f.write(','+first+','+last+'\n')

    for n in range(1, len(ngram_file)):
        ngrams_list = []
        for ngram, count in ngrams_dict[n].items():
            ngrams_list.append((count,ngram))
        ngrams_list.sort(reverse=True)

        with open(ngram_file[n], 'w') as f:
            writer = csv.writer(f)
            writer.writerow([str(n)+'gram', 'count', 'ipm']\
               + (['ipm_from_dict'] if n==1 else []))
            for w in ngrams_list:
                ipm = w[0]*1000000./ngrams_count[n]
                if n==1:
                    an = mystem.lemmatize(w[1])
                    ipm_from_dict = 0.
                    if an[0] in freq_dict:
                        ipm_from_dict = freq_dict[an[0]][0]
                if (n==1) and (an[0][0] in digits):
                    continue
                writer.writerow([w[1], str(w[0]), str(round(ipm, 3))]\
                    + ([str(ipm_from_dict)] if n==1 else []))

def freq_jarg(freq_file, freq_jargon_file):
    df = pd.read_csv(freq_file,
        usecols=['lemma','pos','count','ipm','ipm_from_dict'])
    df = df[df['ipm_from_dict']==0]
    df.to_csv(freq_jargon_file, index=False)

if __name__=='__main__':
    if len(sys.argv) >= 2:
        scrap_file = sys.argv[1]+'_scrap.csv'
        freq_file  = sys.argv[1]+'_freq.csv'
        jargon_file = sys.argv[1]+'_jargon.csv'
        stats_file = sys.argv[1]+'_stats.csv'
        freq_jargon_file = sys.argv[1]+'_freq_jargon.csv'
        N = 1
        if len(sys.argv) >= 3:
            N = int(sys.argv[2])
        ngram_file = [sys.argv[1]+'_'+str(i)+'grams.csv' for i in range(0, N+1)]
    else:
        print("Usage: community/person name as argument.")
        exit()

    freq_jarg_stats(scrap_file, freq_file, ngram_file, jargon_file, stats_file)
    freq_jarg(freq_file, freq_jargon_file)

