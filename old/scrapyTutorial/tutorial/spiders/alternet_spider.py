import scrapy
import re
from urllib.parse import urlparse

'''
TODOs: 
better filtering of non-html files- jacques mattheij is a good counter example, don't want to download .zip files
    maybe just limit the size of the download and delete non-html files after they are downloaded
be able to index the html files as they are downloaded then delete them

'''

def slashToPipe(url):
    return url.replace('/', '|')

def underscoreToPipe(url):
    return url.replace('|', '/')
    

def removeOutsideLinks(linkList, targetUrl):
    internalLinks = []
    n = len(targetUrl)
    targetParse = urlparse(targetUrl)
    for url in linkList:
        #x is an object if the url begins with bitcoin, mailto, or tel
        x = re.search('^bitcoin:|^mailto:|^tel:', url)
        #removes fragments, which are the #blahblah at the end of urls
        '''
        fragment = url.find('#')
        #if there is a fragment
        if fragment != -1:
            url = url[0:fragment]
        #if the whole link is a fragment
        elif fragment = 0:
            continue
        '''
        urlParse = urlparse(url)
        
        #last or excludes non-html links
        if (urlParse.netloc != '' and targetParse.netloc != urlParse.netloc) or x != None:
            #will be outside link
            #print(url, targetUrl, targetParse.netloc, 'url parse:',  urlParse.netloc, targetParse.scheme, urlParse.scheme)
            continue
        
        else:
            internalLinks.append(url)
    #print('targetURL', targetUrl)
    #print('internalLinks', internalLinks)
    #print('linkList', linkList)
    return internalLinks


class AlternetSpider(scrapy.Spider):
    AUTOTHROTTLE_ENABLED = True
    name = "alternet"
    urls = []
    f = open('../urlList.txt', 'r')
    urls = f.read().splitlines()
    f.close()
    urls = ['https://marginalrevolution.com']
    currentUrl = urls[0]

    def start_requests(self):
        for url in self.urls:
            #print("IN START REQUESTS", url)
            #self.currentUrl = url
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        self.log('Parsing %s' % response.url)
        filename = slashToPipe(response.url)
        self.currentUrl = response.url
        with open('../crawledFiles/' + filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
        nextPages = response.css('a::attr(href)').getall() 
        #print("before pruning", nextPages)
        nextPages = removeOutsideLinks(nextPages, self.currentUrl)
        #print('after pruning', nextPages)
        yield from response.follow_all(nextPages, callback=self.parse) 

