import os
import threading
import time
import logging
import sys

def setDiff(first, second):
    second = set(second)
    return [item for item in first if item not in second]

def mergeAndPageRank():
    os.system('python3 merger.py')
    print('done merging')
    #os.system('python3 pageRanker.py')
    #print('done ranking')

def crawl():
    os.system('scrapy crawl alternet')

class MergeThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopped = False

    def run(self):
        while not self.stopped:
            numFiles = len(os.listdir('webIndexCache/'))
            logging.info('started merging and ranking %d files' % numFiles)
            os.system('python3 merger.py')
            #os.system('python3 pageRanker.py')
            logging.info('finished merging and ranking %d files' % numFiles)
            time.sleep(60)

try:
    batchSize = int(sys.argv[1])
except:
    batchSize = 2


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
    print('No urls to crawl')
    exit()
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
        time.sleep(10)
    mergeThread.stopped = True

    os.system('python3 merger.py')
    #os.system('python3 pageRanker.py')
    logging.info('final merging and ranking done')
    with open('urlLists/crawledUrls.txt', 'a') as f:
        for listItem in urlsToCrawl:
            f.write('%s\n' % listItem)
        f.close()
    os.remove('urlLists/urlsToCrawl.txt')



