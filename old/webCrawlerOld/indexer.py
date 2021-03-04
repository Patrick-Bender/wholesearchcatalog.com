from html.parser import HTMLParser
import codecs
import re
from os import listdir
from os.path import isfile,join, splitext, normpath
from os import remove as removeFile
import json


def removeSymbols(data):
    data = re.sub(r'\W+', ' ', data)
    data.replace('\n', ' ')
    data.replace('\t', ' ')
    data.replace('\'', '')
    data = data.lower()
    return data.rstrip()


class HTMLParser(HTMLParser):
    linkIndex = {}
    linkIndexPath = 'linkIndex.json'
    webIndex = {}
    webIndexPath = 'webIndex.json'
    pageIndex = {}
    pageIndexPath = 'pageIndex.json'
    url = ''
    wordPosition = 0
    skipDocument = False
    currentTags = []
    tagsToIgnore = ['script', 'style', 'header', 'footer', 'rss', 'feed']
    tagStartPos  = {
            'title': [],
            'h1': [],
            'h2': [],
            'h3': [],
            'h4': [],
            'h5': [],
            'h6': [],
            'a': [],
            'b': [],
            'blockquote': [],
            'em': [],
            'i': [],
            'li': [],
            'strong': [],
            'table': [],
            'p': []
            }
    def handle_starttag(self, tag, attrs):
        self.currentTags.append(tag)
        if tag in self.tagStartPos:
            self.tagStartPos[tag].append(self.wordPosition)
    def handle_endtag(self, tag):
        try:
            self.currentTags.remove(tag)
            if tag in self.tagStartPos:
                tupleToAdd = (self.tagStartPos[tag][-1], self.wordPosition)
                #to make sure the first part comes before the second part, and to avoid adding tags like <p></p> with no content in them
                if tupleToAdd[0] < tupleToAdd[1]:
                    #add the tuple to pageIndex
                    if self.pageIndex[self.url].get(tag) != None:
                        #if it already exists, append it to existing tag
                        self.pageIndex[self.url][tag].append(tupleToAdd)
                    else:
                        self.pageIndex[self.url][tag] = [tupleToAdd]
                self.tagStartPos[tag].pop()
        except:
            pass
    def handle_data(self, data):
        #ignores data inside of tags in tags to ignore
        if any(item in self.currentTags for item in self.tagsToIgnore):
            pass
        else:
            data = removeSymbols(data)
            words = data.split(' ')
            #deletes all the stopwords 
            stopwords = open('stopwords.txt', 'r')
            #removes words that contains non-ascii characters
            
            if self.pageIndex.get(self.url) == None:
                self.pageIndex[self.url] = {'total':0}
            for line in stopwords:
                for word in words:
                    if line == word + '\n':
                        words.remove(word)
            #iterates through each word in the data
            for word in words:
                #removes words with non-ascii characters
                try:
                    word.encode('utf-8').decode('ascii')
                except UnicodeDecodeError:
                    continue
                #getting '' happens a lot, I don't know why exactly
                if word == '':
                    continue
                #adds new word to index
                elif (self.webIndex.get(word) == None):
                    self.webIndex[word] = {self.url:[self.wordPosition]}
                #if a word is already in the index
                else:
                    #urls is a list of all urls that contain that word
                    #urls = self.webIndex.get(word).keys()
                    #if the url entry for word already exists
                    if self.webIndex[word].get(self.url) != None:
                        self.webIndex[word][self.url].append(self.wordPosition)
                    else:
                        self.webIndex[word][self.url] = [self.wordPosition]
                #Add one to word number index and increment wordPosition by one
                self.pageIndex[self.url]['total'] += 1
                self.wordPosition += 1
        

def indexHTML(parser, HTMLPath, indexPath, url):
    f = codecs.open(HTMLPath, 'r')
    
    try:
        parser.url = url
        parser.feed(f.read())
        #if the document contains fewer than 10 words, remove it
        if parser.wordPosition < 10:
            print('Document not long enough: ', url)
            parser.skipDocument = True 
        return True
    except KeyboardInterrupt:
        exit()
    except UnicodeDecodeError:
        f.close()
        removeFile(HTMLPath)
        return False
    except Exception as error:
        print('something catastraphoic has happened')
        print(error, HTMLPath)
        exit()


