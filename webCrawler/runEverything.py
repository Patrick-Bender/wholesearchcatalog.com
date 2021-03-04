import os
import threading
import time
import logging
import sys
import pymongo
from merger import mergeWebIndex, mergePageIndex
#from pageRanker import pageRank

def setDiff(first, second):
    second = set(second)
    return [item for item in first if item not in second]

def crawl():
    os.system('scrapy crawl alternet')

class MergeThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopped = False

    def run(self):
        while not self.stopped:
            time.sleep(5)
            numFiles = len(os.listdir('webIndexCache/'))
            logging.info('started merging and ranking %d files' % numFiles)
            mergeWebIndex(myClient, 'webIndexCache/')
            logging.info('finished merging web index')
            mergePageIndex(myClient, 'pageIndexCache/', 'linkIndexCache/')
            logging.info('finished merging page index')
            #pageRank(myClient)
            logging.info('finished merging and ranking %d files' % numFiles)

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


urlsToCrawl = setDiff(masterUrlList, crawledUrls)[:batchSize]
logging.info(urlsToCrawl)

if urlsToCrawl == []:
    #removes everything in the crawled urls file
    print('No urls to crawl')
    os.remove('urlLists/crawledUrls.txt')
    open(x, 'a').close()
else:
    with open('urlLists/urlsToCrawl.txt', 'a') as f:
        for listItem in urlsToCrawl:
            f.write('%s\n' % listItem)
        f.close()

    crawlThread = threading.Thread(target=crawl, args = ())
    mergeThread = MergeThread()
    crawlThread.start()
    mergeThread.start()
    while crawlThread.isAlive():
        time.sleep(5)
    mergeThread.stopped = True
    logging.info('waiting for crawl thread to join')
    crawlThread.join() 
    logging.info('doing final merge and rank')
    with open('urlLists/crawledUrls.txt', 'a') as f:
        for listItem in urlsToCrawl:
            f.write('%s\n' % listItem)
        f.close()
    os.remove('urlLists/urlsToCrawl.txt')
    mergeThread.join()
    logging.info('final merge and rank done')



