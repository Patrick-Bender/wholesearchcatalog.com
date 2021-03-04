import os
import pymongo
import json
import time


myClient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")

webdb = myClient['webIndex']
masterWordList = set(webdb.list_collection_names())
for filename in os.listdir('webIndexCache/'):
    if not filename.endswith('.json'):
        print('non-json file: ' + filename)
        continue
    f = open('webIndexCache/' + filename)
    partialIndex = json.load(f)
    #print('merging web index: ' + filename)
    for partialIndexWord in partialIndex.keys():
        #can't make collection with name more than 120, setting it to 110 just to be safe
        if len(partialIndexWord)>110:
            continue
        #This line is pretty complicated, but we always know there will be only one url for the partial index since it's only crawling one url at a time
        #most of the line is just to get the url from a dict_keys object to a string
        url = list(partialIndex[partialIndexWord].keys())[0]
        collection = webdb[partialIndexWord]
        try:
            collection.replace_one({'url': url}, {'url': url, 'location': partialIndex[partialIndexWord][url], 'lastUpdated': time.time()}, upsert=True)
        except KeyboardInterrupt:
            break
    os.remove('webIndexCache/' + filename)

print('completed web index merge')

pagedb = myClient['pageIndex']
for filename in os.listdir('pageIndexCache/'):
    if not filename.endswith('.json'):
        print('non-json file: ' + filename)
        continue
    f = open('pageIndexCache/' + filename)
    partialIndex = json.load(f)
    #print('merging page index: ' + filename)
    url = list(partialIndex.keys())[0]
    if len(url)>110:
        continue
    collection = pagedb[url]
    for tag in partialIndex[url]:
        try:
            collection.replace_one({'tag': tag}, {'tag': tag, 'values': partialIndex[url][tag], 'lastUpdated': time.time()}, upsert=True)
        #necessary to stop db from being corrupted
        except KeyboardInterrupt:
            break

    os.remove('pageIndexCache/' + filename)

print('completed page index merge')

for filename in os.listdir('linkIndexCache/'):
    if not filename.endswith('.json'):
        print('non-json file: ' + filename)
        continue
    f = open('linkIndexCache/' + filename)
    partialIndex = json.load(f)
    #print('merging links: ' + filename)
    url = list(partialIndex.keys())[0]
    if len(url)>110:
        continue
    collection = pagedb[url]
    try:
        collection.replace_one({'tag': 'links'}, {'tag': 'links', 'values': partialIndex[url], 'lastUpdated': time.time()}, upsert=True)
    except KeyboardInterrupt:
        break
    os.remove('linkIndexCache/' + filename)
