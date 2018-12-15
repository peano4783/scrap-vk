import json
import requests
import pandas as pd
from time import sleep
import sys

def read_access_token(filename = 'access_token'):
    "В файле хранится ключ доступа к ВКонтакте"
    with open(filename) as f:
        for line in f:
            return line.rstrip()

access_token_ver = 'access_token='+read_access_token()+'&v=5.73'

def json_scrap_url(url, max_attempts=10, sleep_interval=0.5):
    "Функция для отправки запроса и разбора ответа"
    attempts = 0
    while True:
        r = requests.get(url)
        json_data = json.loads(r.text)
        if 'response' in json_data:
            return(json_data['response'])
        attempts += 1
        if attempts > max_attempts:
            return(None)
        sleep(sleep_interval)

def write_comment(f, tp, timestamp, author, text):
    text = str(text).replace('\n',' . ').replace('"', "''")
    f.write(tp+','+str(timestamp)+','+str(author)+',"'+text+'"\n')

def parse_wall(owner_id, owner_name):
    "Разбираем сообщения на стене группы"
    comment_count = 0
    offset = 12200

    f = open(owner_name + '_scrap.csv', 'w')
    f.write('type,timestamp,author,text\n')

    wall = {'count': offset+100}
    while offset <= wall['count']:
        wall = json_scrap_url('https://api.vk.com/method/wall.get?'+
            access_token_ver+'&extended=0&owner_id='+owner_id+'&count=100&offset='+str(offset))
        for t in wall['items']:
            write_comment(f, 'p', t['date'], t['from_id'], t['text'])
            # Разбираем комментарии к каждому сообщению:
            if t['comments']['count'] == 0:
                continue
            comment_count += t['comments']['count']
            coffset = 0
            while coffset <= t['comments']['count']:
                comment = json_scrap_url('https://api.vk.com/method/wall.getComments?'+
                    access_token_ver+'&extended=0&owner_id='+owner_id+'&count=100'+
                   '&offset='+str(coffset)+'&post_id='+str(t['id']))
                for tc in comment['items']:
                    write_comment(f, 'c', tc['date'], tc['from_id'], tc['text'])
                coffset += 100
        print('offset = ', offset, ' of ', wall['count'], ' posts')
        print('comment_count = ', comment_count)
        offset += 100
    f.close()



if __name__=='__main__':
    #owner_id, owner_name = '-2258508', 'capoeirakazan'
    owner_id, owner_name = '-38959783', 'kzngo'
    #owner_id, owner_name = '1', 'paveldurov'
    if len(sys.argv) == 3:
        owner_id, owner_name = sys.argv[1], sys.argv[2]
    parse_wall(owner_id, owner_name)


# python3 scrap_vk_wall.py -38959783 kzngo
# python3 scrap_vk_wall.py -34215577 podslush
# python3 scrap_vk_wall.py -272 kazanushka
