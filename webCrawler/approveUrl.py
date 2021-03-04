import os
import logging
import sys

try:
    batchSize = int(sys.argv[1])
except:
    batchSize = 1
#get urls to add
with open('urlLists/urlsToAdd.txt', 'r') as f:
    urlsToAdd = f.read().splitlines()
    f.close
#add urls to masterUrlList
print('approving: ' + str(urlsToAdd[:batchSize]))
with open('urlLists/masterUrlList.txt', 'a') as f:
    for url in urlsToAdd[:batchSize]:
        f.write(url + '\n')
    f.close()

#remove the urls we are adding
os.remove('urlLists/urlsToAdd.txt')
with open('urlLists/urlsToAdd.txt', 'w+') as f:
    for url in urlsToAdd[batchSize:]:
        f.write(url + '\n')
    f.close()
