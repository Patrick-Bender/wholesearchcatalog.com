from ast import literal_eval
import json
import re
import time
from math import log, erf
import sys
import pymongo
from urllib.parse import urlparse
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer



def removeSymbols(data):
    data = re.sub(r'\W+', ' ', data)
    data.replace('\n', ' ')
    data.replace('\t', ' ')
    data.replace('\'', ' ')
    data = data.lower()
    return data.rstrip()

def parseQuery(self, query):
    #same treatment that new words get in the crawler
    print('query: ', query, type(query))
    query = removeSymbols(query)
    query = word_tokenize(query)
    stop_words = set(stopwords.words('english'))
    query = [word for word in query if not word in stop_words]
    ps = PorterStemmer()
    query = [ps.stem(word) for word in query]
    return query

def logQuery(query, logdb, startTime, searchTime=-1):
    if query.startswith('~'):
        return False
    logdb['queries'].replace_one({'query': query, 'time': startTime}, {'query': query, 'searchTime': searchTime, 'time': startTime}, upsert=True)


def sortResult(result):
    startTime = time.time()
    mapping = {r[1]:r[0] for r in result}
    scores = [r[1] for r in result]
    scores = sorted(scores)
    result = [[mapping[score], score] for score in scores]
    result = result[::-1]
    print('sort result took', time.time()-startTime)
    return result


def derankRepeatedDomains(sortedResult, derankFactor):
    domainCounter = {}
    for i in range(len(sortedResult)):
        result = sortedResult[i]
        url = result[0]
        score = result[1]
        parser = urlparse('https://' + url)
        try: domainCounter[parser.netloc] += 1
        except KeyError: domainCounter[parser.netloc] = 1
        if domainCounter[parser.netloc]>1:
            sortedResult[i][1] -= derankFactor*domainCounter[parser.netloc]
    return sortedResult

#needs to not be a method since it's called on the instantiation of the searcher class
def getTotalScore(url, pagedb, weightDict):
    pageIndex = list(pagedb[url].find())
    totScore = 0
    for doc in pageIndex:
        if doc['tag'] in weightDict:
            locations = doc['values']
            for location in locations:
                totScore += (location[1]-location[0]+1)*weightDict[doc['tag']]
    return totScore
 
def intersect(documents):
    #searchUrls has format {'word1':['url','url'], 'word2':['url','url']}
    searchUrls = {}
    for word in documents.keys():
        searchUrls[word] = []
        for page in documents[word]:
            searchUrls[word].append(page['url'])
    #values gives a flattened list of all urls that show up
    allUrls = [j for sub in searchUrls.values() for j in sub]
    #removes duplicate values
    allUrls = list(dict.fromkeys(allUrls)) 
    #urls is a list of all the urls that contain all the words in the query
    urls = [url for url in allUrls if all(url in searchUrls[word] for word in searchUrls.keys())]
    return urls

class Searcher():
    startTime = time.time()
    weightDict = {
            'title': 200,
            'h1': 10,
            'h2': 10,
            'h3': 9,
            'h4': 8,
            'h5': 7,
            'h6': 6,
            'a': 3,
            'b': 4,
            'blockquote': 4,
            'em': 4,
            'i': 4,
            'strong': 4,
            'table': 1,
            'body':1
            }

    client = pymongo.MongoClient()
    webdb = client['webIndex']
    pagedb = client['pageIndex']
    logdb = client['logs']
    #update things that are older than 2 days
    updateAge = 172800
    #note when I switch up the architecture I will want to revisit this line to make sure N is up to date
    N = len(pagedb.list_collection_names())
    k_1 = 1.2
    k_2 = 100
    b = 0.75
    #calculates average document length
    startTime = time.time()
    totalScore = 0
    for collection in pagedb.list_collection_names():
        document = pagedb[collection].find_one({'tag': 'totScore'})
        try: docAge = time.time()-document[lastUpdated]
        except: docAge = 0
        if type(document) == type(None) or docAge<updateAge:
            docScore = getTotalScore(collection, pagedb, weightDict)
            document = {'tag':'totScore', 'values': docScore, 'lastUpdated': time.time()}
            pagedb[collection].replace_one({'tag': 'totScore','values': docScore}, document, upsert = True)
        totalScore += document['values'] 
    avgds = totalScore/N
    print('getting average doc score took', time.time()-startTime)
    derankFactor = 0.1
        
    def BM25(self, query, url, f, ds, n, R = 0, r = 0):
        if r == 0:
            r = {key:0 for key in query}
        k_1 = self.k_1
        k_2 = self.k_2
        b = self.b
        N = self.N
        avgds = self.avgds
        result = 0
        qf = {}
        for word in query:
            try: qf[word] += 1
            except KeyError: qf[word] = 1
        for i in range(len(query)):
            word = query[i]
            r_i = r[word]
            qf_i = qf[word]
            n_i = n[word]
            f_i = f[word]
            #f_i = len(wordLocations)/total
            K = k_1*((1-b)+b*ds/avgds)
            idf = log(((r_i+0.5)/(R-r_i+0.5))/((n_i+r_i+0.5)/(N-n_i-R+r_i+0.5)))
            tf = (((k_1+1)*f_i)/(K+f_i))*(((k_2+1)*qf_i)/(k_2+qf_i))
            result += idf*tf
        return result
    
    def scoreUrls(self, query, urls):
        #generate web index
        n = {}
        webIndex = {}
        pageIndex = {}
        result = {}
        total = {}
        locationAndTagInfo = {}
        weightCounter = {}
        webIndexStartTime = time.time()
        for word in query:
            #normally you could use dict.fromkeys(query,{}), but that refers to a single instance so you need to iterate through the for loop otherwise things get wonky
            locationAndTagInfo[word] = {}
            collection = list(self.webdb[word].find())
            collection2 = collection[:]
            n[word] = len(collection)
            #i have no idea why but after the keys assignment collection = []
            #so i need to redeclare collection2 for some godforsaken reason, and also it need to add [:] becuase otherwise it will just be a reference to collection rather than it's own thing
            keys = [entry['url'] for entry in collection]
            values = [entry['location'] for entry in list(collection2)]
            #this alone would leave them out of order
            #values = [entry['location'] for entry in list(collection) if entry['url'] in urls]
            webIndex[word] = dict((url,location) for url,location in zip(keys,values))
            #web index is {'word': {url:location, url:location}, 'word2':{url:location, url:location}}
        print('generating webIndex took', time.time()-webIndexStartTime)
        #generate pageIndex
        pageIndexStartTime = time.time()
        test = 0
        for url in urls:
            result[url] = 0
            startTime = time.time()
            collection = list(self.pagedb[url].find())
            test += time.time()-startTime
            collection2 = collection[:]
            '''
            for entry in collection:
                if entry['tag'] == 'total':
                    total[url] = entry['values']
           '''
            keys = [entry['tag'] for entry in collection]
            values = [entry['values'] for entry in collection2]
            pageIndex[url] = dict((tag,values) for tag, values in zip(keys, values) if (tag in self.weightDict or tag == "totScore"))
            #page index is {'url':{'tag':values, 'tag':values, 'tag':values}, 'url':{'tag':values', 'tag':values}}
        print('test', test)
        print('generating pageIndex took', time.time()-pageIndexStartTime)
        weightCounterStartTime = time.time()
        for word in query:
            #print('web index keys for word:', word, webIndex[word].keys())
            weightCounter[word] = {}
            for url in urls:
                try: wordLocations = webIndex[word][url]
                except: continue
                weightCounter[word][url] = 0
                locationAndTagInfo[word][url] = {}
                for tag in pageIndex[url].keys():
                    if tag == 'totScore':
                        continue
                    tagLocations = pageIndex[url][tag]
                    for wordLocation in wordLocations:
                        for tagLocation in tagLocations:
                            if tagLocation[0]<=wordLocation and wordLocation<=tagLocation[1]:
                                '''
                                if not wordLocation in locationAndTagInfo[word][url].keys():
                                    locationAndTagInfo[word][url][wordLocation] = set()
                                    #if you call set(tag) then it creates a set of characters rather than a set of strings
                                    locationAndTagInfo[word][url][wordLocation].add(tag)
                                else:
                                    locationAndTagInfo[word][url][wordLocation].add(tag)
                                '''
                                weightCounter[word][url] += self.weightDict[tag]
                                continue
        print('generating weight counter and tag locations took', time.time()-weightCounterStartTime)
        scoringStartTime = time.time()
        for url in urls:
            if pageIndex[url] == {}:
                continue
           # for word, key in weightCounter.items():
                #print(word, key)
            #query, url, f = {'word':freq, 'word':freq}, dl = doc length ('tag':total', n
            f = {}
            for word in query:
                try: f[word] = weightCounter[word][url]
                except: f[word] = 0
            #f = {word:key[url] for word,key in weightCounter.items()}
            #will sometimes give an error if page index doens't exit, so I'm wrappigng it in a try except statement to stop that
            try:ds = pageIndex[url]['totScore']
            except: continue
            #get n from generation of web index
            result[url] = self.BM25(query, url, f, ds, n)
        print('scoring took', time.time()-scoringStartTime)
        return result
        
    def getResults(self, query, urls):
        startTime = time.time()
        result = {}
        result = self.scoreUrls(query, urls)
        print('score urls took: ', time.time()-startTime)
        result = [[key,value] for (key,value) in result.items() if value>0]
        test = 0
        '''
        for key in result:
            if key.startswith('ergoemacs.org'):
                test += 1
                print('found one', key, result[key])
            if key == 'ergoemacs.org/emacs/blog_past_2015-06_2015-06.html':
                print('stop:', test)
        print('result', 'ergoemacs.org/emacs/blog_past_2015-06_2015-06.html', result['ergoemacs.org/emacs/blog_past_2015-06_2015-06.html'])
        '''
        startTime = time.time()
        result = sortResult(result)
        result = derankRepeatedDomains(result, self.derankFactor)
        result = sortResult(result)
        print('sorting, deranking, then resorting took', time.time()-startTime)
        
        return result
   
    
    def search(self, query):
        searchStartTime = time.time()
        queryCopy = query[:]
        logQuery(queryCopy, self.logdb, searchStartTime)
        query = parseQuery(self, query)
        print('pared query', query)
        documents = {}
        termWeight = {}
        #failedWords are words that don't exist in any crawled files
        failedWords = []
        for word in query:
            #list of all entries in the word collection
            docList = list(self.webdb[word].find({}))
            if docList != []:
                documents[word] = docList
            else:
                failedWords.append(word)
        if failedWords != []:
            for failedWord in failedWords:
                query.remove(failedWord)
        #if intersect stops working this will give you all the urls
        
        '''
        urls = set()
        for word in documents:
            for document in documents[word]:
                urls.add(document['url'])
        urls = list(urls)
        '''
        urls = intersect(documents)
        #if there are no urls with all the words, just include all the urls with any of the words
        if urls == []:
            urls = set()
            for word in documents:
                for document in documents[word]:
                    urls.add(document['url'])
            urls = list(urls)
        #url cannot contain $, otherwise it throws a key error from mongo
        urls = [url for url in urls if not '$' in url]
        searchResults = self.getResults(query, urls)
        searchTime = time.time()-searchStartTime
        logQuery(queryCopy, self.logdb, searchStartTime, searchTime)
        return searchResults, searchTime


#def searchIndex(webIndex, pageIndex, query):
'''
searcher = Searcher()
try:
    query = sys.argv[1]
except:
    query = 'blavamorphic bender'
startTime = time.time()
print(searcher.search(query))
print('search took %s seconds' % str(time.time()-startTime))
#print(searcher.search('polymorphic'))
'''
