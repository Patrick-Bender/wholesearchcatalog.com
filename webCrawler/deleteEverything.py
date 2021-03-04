import os
import pymongo

print('running delete everything')

client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
print('dropping webIndex')
client.drop_database('webIndex')
print('dropping pageIndex')
client.drop_database('pageIndex')

print('deleting caches')

for filename in os.listdir('linkIndexCache'):
    os.remove('linkIndexCache/'+filename)

for filename in os.listdir('webIndexCache'):
    os.remove('webIndexCache/'+filename)

for filename in os.listdir('pageIndexCache'):
    os.remove('pageIndexCache/'+filename)

print('deleting urls to crawl and crawled urls')

try:
    os.remove('urlLists/urlsToCrawl.txt')
except:
    pass

try:
    os.remove('urlLists/crawledUrls.txt')
except:
    pass

