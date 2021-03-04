import sys
import os

try: batchSize = int(sys.argv[1])
except: batchSize = 1

with open('urlLists/urlsToAdd.txt', 'r') as f:
    urlsToAdd = f.read().splitlines()
    f.close
os.remove('urlLists/urlsToAdd.txt')
print('denying ', urlsToAdd[:batchSize])
with open('urlLists/urlsToAdd.txt', 'w+') as f:
    for url in urlsToAdd[batchSize:]:
        f.write(url + '\n')
    f.close()

