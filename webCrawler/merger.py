import os
import pymongo
import json
import time
import logging

def mergeWebIndex(myClient, cachePath):
    numWords = 0
    globalStart = time.time()
    webdb = myClient['webIndex']
    test = 0
    try: masterWordList = set(webdb.list_collection_names())
    except pymongo.errors.ServerSelectionTimeoutError as error:
        print('mongo server is down', error)
        exit()
    for filename in os.listdir(cachePath):
        fileStartTime = time.time()
        logging.debug('starting webIndex merge of : ' + filename)
        if not filename.endswith('.json'):
            logging.info('non-json file: ' + filename)
            continue
        f = open(cachePath + filename)
        partialIndex = json.load(f)
        #print('merging web index: ' + filename)
        for partialIndexWord in partialIndex.keys():
            #can't make collection with name more than 120 chars, setting it to 117 just to be safe
            if len(partialIndexWord)>117:
                continue
            #This line is pretty complicated, but we always know there will be only one url for the partial index since it's only crawling one url at a time
            #most of the line is just to get the url from a dict_keys object to a string
            url = list(partialIndex[partialIndexWord].keys())[0]
            collection = webdb[partialIndexWord]
            testStartTime = time.time()

            try: collection.replace_one({'url': url}, {'url': url, 'location': partialIndex[partialIndexWord][url], 'lastUpdated': time.time()}, upsert=True)
            except KeyboardInterrupt: exit()
            except Exception as error: 
                print(error)
                continue
            test += time.time()-testStartTime
        logging.debug('completed webIndex merge of : ' + filename)
        logging.debug(filename + ' took ' + str(time.time()-fileStartTime))
        logging.debug('test:' + str(test))
        try: os.remove(cachePath + filename)
        except: pass
    logging.info('completed webIndex merge')


def mergePageIndex(myClient, pageCachePath, linkCachePath):
    pagedb = myClient['pageIndex']
    for filename in os.listdir(pageCachePath):
        if not filename.endswith('.json') or '$' in filename:
            logging.info('non-json file or $ in filename: ' + filename)
            os.remove(pageCachePath + filename)
            continue
        f = open(pageCachePath + filename)
        partialIndex = json.load(f)
        
        #print('merging page index: ' + filename)
        try: url = list(partialIndex.keys())[0]
        except IndexError: 
            logging.info('found wrong file in pageIndexMerge: '+ filename + ' partial index:' + str(partialIndex))
            os.remove(pageCachePath + filename)
            continue
	#can't make collection with name more than 120 chars, setting it to 117 just to be safe
        if len(url)>117:
            continue
        collection = pagedb[url]
        for tag in partialIndex[url]:
            try: collection.replace_one({'tag': tag}, {'tag': tag, 'values': partialIndex[url][tag], 'lastUpdated': time.time()}, upsert=True)
            except KeyboardInterrupt: exit()
            except: continue
        logging.debug('completed pageIndex merge of : ' + filename)
        try: os.remove(pageCachePath + filename)
        except: pass
    logging.info('completed pageIndex merge')

    for filename in os.listdir(linkCachePath):
        if not filename.endswith('.json') or '$' in filename:
            logging.info('non-json file or $ in filename: ' + filename)
            os.remove(linkCachePath + filename)
            continue
        f = open(linkCachePath + filename)
        partialIndex = json.load(f)
        #print('merging links: ' + filename)
        try: url = list(partialIndex.keys())[0]
        except IndexError:
            logging.info('found wrong file in linkIndexMerge: '+ filename + ' partial index:' + str(partialIndex))
            os.remove(linkcachePath + filename)
            continue
        if len(url)>117:
            continue
        collection = pagedb[url]
        try:collection.replace_one({'tag': 'links'}, {'tag': 'links', 'values': partialIndex[url], 'lastUpdated': time.time()}, upsert=True)
        except KeyboardInterrupt: exit()
        except: continue
        logging.debug('completed linkIndex merge of : ' + filename)
        try: os.remove(linkCachePath + filename)
        except: pass
    logging.info('completed linkIndex merge')

format = '%(asctime)s: %(message)s'
logging.basicConfig(format=format, level=logging.INFO, datefmt='%H:%M:%S')
client = pymongo.MongoClient('') #insert mongo client uri here format is 'mongodb://crawler:password@localhost:27017/'
print('started merging web index')
mergeWebIndex(client, 'webIndexCache/')
print('started merging page index')
mergePageIndex(client, 'pageIndexCache/', 'linkIndexCache/')
