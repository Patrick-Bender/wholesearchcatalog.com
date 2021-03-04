import os
import threading
import time
import logging
import sys
import pymongo
from urllib.parse import urlparse

def setDiff(first, second):
    second = set(second)
    return [item for item in first if item not in second]

def crawl():
    os.system('scrapy crawl alternet')

try:
    batchSize = int(sys.argv[1])
except:
    batchSize = 1

myClient = pymongo.MongoClient('mongodb://localhost:27017/')

format = '%(asctime)s: %(message)s'
logging.basicConfig(format=format, level=logging.INFO, datefmt='%H:%M:%S')
with open('urlLists/masterUrlList.txt', 'r') as f:
    masterUrlList = f.read().splitlines()
    f.close()
if not os.path.exists('urlLists/crawledUrls.txt'):
    f = open('urlLists/crawledUrls.txt', 'w+')
    f.close()
with open('urlLists/crawledUrls.txt', 'r') as f:
    crawledUrls = f.read().splitlines()
    f.close()
with open('urlLists/urlsToAdd.txt', 'r') as f:
    urlsToAdd = f.read().splitlines()
    f.close()
#TODO: make it such that it looks at netloc rather than raw string
#remove redundant urls
urlsToAdd = setDiff(urlsToAdd, masterUrlList)
os.remove('urlLists/urlsToAdd.txt')
with open('urlLists/urlsToAdd.txt', 'w+') as f:
    for url in urlsToAdd:
        f.write(url + '\n')
    f.close()
urlsToTest = urlsToAdd[:batchSize]

logging.info(urlsToTest)


if urlsToTest == []:
    print('No urls to add')
    exit()
else:
    with open('urlLists/urlsToCrawl.txt', 'a') as f:
        for listItem in urlsToTest:
            f.write('%s\n' % listItem)
        f.close()
    crawl()
    os.remove('urlLists/urlsToCrawl.txt')
    for cacheLocation in ['webIndexCache/', 'pageIndexCache/', 'linkIndexCache/']:
        fileList = [f for f in os.listdir(cacheLocation)]
        for f in fileList:
            os.remove(os.path.join(cacheLocation, f))



