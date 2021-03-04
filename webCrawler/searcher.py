from ast import literal_eval
import json
import re
import time
from math import log, erf
import sys
import pymongo
def removeSymbols(data):
    data = re.sub(r'\W+', ' ', data)
    data.replace('\n', ' ')
    data.replace('\t', ' ')
    data.replace('\'', ' ')
    data = data.lower()
    return data.rstrip()

def removeStopwords(words):
    stopwords = open('stopwords.txt', 'r')
    for line in stopwords:
        for word in words:
            if line == word + '\n':
                words.remove(word)
    return words

def parseQuery(query):
    #same treatment that new words get in the crawler
    query = removeSymbols(query)
    query = query.split(' ')
    query = removeStopwords(query)
    '''
    wordCombos = []
    for i in range(len(query)):
        for j in range(i+1, len(query)):
            wordCombos.append(query[i] + 
    '''
    return query

def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2)) 
class searcher():
    startTime = time.time()
    client = pymongo.MongoClient()
    webdb = client['webIndex']
    pagedb = client['pageIndex']
    weightDict = {
            'title': 20,
            'h1': 20,
            'h2': 10,
            'h3': 7,
            'h4': 5,
            'h5': 4,
            'h6': 3,
            'a': 2,
            'b': 3,
            'blockquote': 2,
            'em': 3,
            'i': 2,
            'li': 2,
            'strong': 3,
            'table': 2,
	    'p':1
            }

    def scoreDoc(self, query, document):
        #I coded most of this at 11:30 while at the ballmer peak so good luck figuring out what's happening
        #Also I would like to acknowledge the extra-dimensional beings that helped me out on this one, they really did me a solid
        print('document', document)
        result = 0
        url = document['url']
        pageIndex = list(self.pagedb[url].find())
        total = self.pagedb[url].find_one({'tag':'total'})['values']
        for entry in pageIndex:
            if entry['tag'] in ['total', 'links', 'pageRank']:
                pageIndex.remove(entry)
        if len(query) == 0:
            return []
        elif len(query) == 1:
            word = query[0]
            #wordLocations is a list of all the positions where the word appears
            wordLocations = document.get('location')
            if wordLocations == None:
                return []
            for entry in pageIndex:
                tag = entry['tag']
                if tag in self.weightDict:
                    #this is a goddamn unholy ambomination forged in the fires of mordor, but it works somehow
                    for tagLocation in list(self.pagedb[url].find({'tag':tag}))[0]['values']:
                        #problem- only looking at location of first word
                        for wordLocation in wordLocations:
                            if tagLocation[1]<wordLocation or tagLocation[0]>wordLocation:
                                pass
                            else:
                                result += self.weightDict[tag]
                                continue
        #for multiword queries, scores how far apart the words are
        else:
            #ex. for a 3 word query gives [{},{},{}]
            #structure is [{location: [tags], location:[tags]}, {location:[tags]}]
            #originally had line that said locationAndTagInfo = [{}]*len(query), but it turns out if you modify one dictionary in the list then that modifies all of them for some godforsaken reason
            #so instead I appended a {} for each word
            locationAndTagInfo = []
            for i in range(len(query)):
                locationAndTagInfo.append({})
                word = query[i]
                wordLocations = document.get('location')
                if wordLocations == None:
                    continue
                #builds locationAndTagInfo
                for entry in pageIndex:
                    tag = entry['tag']
                    if tag == 'total':
                        pass
                    else:
                        if tag in self.weightDict:
                            for tagLocation in list(self.pagedb[url].find({'tag':tag}))[0]['values']:
                                for wordLocation in wordLocations:
                                    #if word location is in the tag
                                    if tagLocation[0]<=wordLocation and wordLocation<=tagLocation[1]:
                                        if locationAndTagInfo[i].get(wordLocation) == None:
                                            #print('new word location', i, wordLocation, tag)
                                            locationAndTagInfo[i][wordLocation] = [tag]
                                        else:
                                            #print('appending new word location', i, wordLocation, tag)
                                            locationAndTagInfo[i][wordLocation].append(tag)
                                        continue 
            

            #turn location and tag info into a real number result
            print('loc and tag info', locationAndTagInfo)
            for i in range(len(locationAndTagInfo)):
                currentWord = locationAndTagInfo[i]
                for location in currentWord:
                    x = location
                    xweight = 0
                    for tag in currentWord[location]:
                        xweight += self.weightDict[tag]
                    for j in range(i+1, len(locationAndTagInfo)):
                        for secondLocation in locationAndTagInfo[j]:
                            y = secondLocation
                            yweight = 0
                            for tag2 in locationAndTagInfo[j][secondLocation]:
                                yweight+= self.weightDict[tag2]
                            result += (xweight+yweight)/abs(x-y)

        #divide by total number of words on the page so to make it more likely that one specific blog post comes up rather than a feed of many blog posts
            #print('loc and tag', document, locationAndTagInfo)
        #
        result /= total
        return result

    
    def sortResults(self, result):
        myList = []
        for key in result:
            myList.append([key, result[key]])
        #uses quicksort, can definitely be made more efficient if that becomes an issue
        for i in range(len(myList)-1):
            for j in range(0, len(myList)-i-1):
                if myList[j][1]<myList[j+1][1]:
                    myList[j], myList[j+1] = myList[j+1], myList[j]
        return myList
            
    def ranking(self, query, documents):
        result = {}
        for word in documents:
            for document in documents[word]:
                score = self.scoreDoc(query,document)
                #TODO: fix page ranker
                pageRankScore = 1
                if score <= 0:
                    continue
                else:
                    result[document['url']] = log(score*pageRankScore*(10**5))
        return self.sortResults(result)

    def search(self, query):
        startTime = time.time()
        query = parseQuery(query)
        documents = {}
        
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
        searchResults = self.ranking(query, documents)
        searchTime = time.time()-startTime
        return searchResults, searchTime


#def searchIndex(webIndex, pageIndex, query):

searcher = searcher()
try:
    query = sys.argv[1]
except:
    query = 'blavamorphic bender'
startTime = time.time()
print(searcher.search(query))
print('search took %s seconds' % str(time.time()-startTime))
#print(searcher.search('polymorphic'))
