import scrapy
import re
import logging
#if json loading and saving ever becomes too slow for project, switch to message pack, it's about 10 time faster
import json
import os
import time
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen
from indexer import indexHTML, HTMLParser


def slashToPipe(url):
    return url.replace('/', '|')

def underscoreToPipe(url):
    return url.replace('|', '/')
    
def validateUrl(url):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc, result.path])
    except:
        return False

def relativeToAbsoluteUrl(base_url, relative_url):
    if type(base_url) == str and type(relative_url) == str:
        return urljoin(base_url, relative_url)
    elif type(base_url) == str and type(relative_url) == list:
        myList = []
        toReturn = []
        for rel_url in relative_url:
            myList.append(urljoin(base_url, rel_url))
        for url in myList:
            urlParse = urlparse(url)
            if urlParse.scheme == 'https' or urlParse.scheme == 'http':
                toReturn.append(url)
        return toReturn
    elif type(base_url) == list and type(relative_url) == list and len(base_url) == len(relative_url):
        myList = []
        for i in range(len(base_url)):
            myList.append(urljoin(base_url[i], relative_url[i]))
        return myList
    else:
        logging.CRITICAL('something has gone wrong with relativeToAbsoluteUrl')
        logging.CRITICAL(base_url, relative_url, type(base_url), type(relative_url))
        exit()
        


def isUrlInUniverse(self, url, urlMasterList):
    urlParse = urlparse(url)
    for universeUrl in urlMasterList:
        #if there's a blank line somewhere in the url document it will say everything is in the universe because everything starts with ''
        if universeUrl == '':
            continue
        universeParse = urlparse(universeUrl)
        #if (universeParse.netloc + universeParse.path) in (urlParse.netloc + urlParse.path +'/'): 
        urlPart = urlParse.netloc + urlParse.path
        universePart = universeParse.netloc + universeParse.path
        if (urlPart).startswith(universePart) or (urlPart).startswith('www.' + universePart) or (urlPart+'/').startswith(universePart) :
            return True
    self.logger.debug('Found link not in universe: %s' % url)
    return False

def removeOutsideLinks(self, linkList, targetUrl, urlMasterList):
    internalLinks = []
    n = len(targetUrl)
    targetParse = urlparse(targetUrl)
    for url in linkList:
        #removes fragments, which are the #blahblah at the end of urls
        fragment = url.find('#')
        #if there is a fragment
        if fragment != -1:
            url = url[0:fragment]
            #to ensure that it's not double counting links
            if url in linkList:
                continue
        #if the whole link is a fragment
        elif fragment == 0:
            continue
        #x is an object if the url begins with bitcoin, mailto, or tel
        x = re.search('^bitcoin:|^mailto:|^tel:', url)
        urlParse = urlparse(url)
        #will be outside link
        if (urlParse.netloc != '' and urlParse.netloc + urlParse.path not in targetParse.netloc + targetParse.path + '/') or x != None:
            if isUrlInUniverse(self, url, urlMasterList):
                internalLinks.append(url)
            else:
                self.logger.debug('removing outside link' + url + ' found in ' +  targetUrl)
        else:
            internalLinks.append(url)
    return internalLinks

def removeBadFileLinks(self, linkList):
    allowedFiles = ('html', 'txt', 'htm', 'asp')
    #if you edit linkList instead of allowedLinks, you skip over every other link since your removing links as you iterate through it
    #it took me like an entire day to figure this one out
    allowedLinks = []
    for link in linkList:
        path = urlparse(link).path
        name = path.rsplit('/', 1)[-1]
        if '.' in name:
            ext = path.rsplit('.',1)[-1]
            if ext in allowedFiles:
                allowedLinks.append(link)
            else:
                self.logger.debug('Removing bad file %s, in url %s' % (link, self.currentUrl))
        else:
            allowedLinks.append(link)

    return allowedLinks



def removeRepeatedLinks(linkList):
    return list(set(linkList))

def removeSelfLinks(self, linkList, url):
    for link in linkList:
        if url == link:
            self.logger.debug("Found self link: %s" % link) 
            linkList.remove(url)
    return linkList

def isUrlBanned(link, bannedUrl):
    workingLink = link
    for urlPart in bannedUrl:
        endIndex = workingLink.find(urlPart)
        if endIndex == -1:
            return False
        else:
            workingLink = workingLink[endIndex+len(urlPart):]
    return True

def removeBannedUrls(self, linkList, bannedUrls, bannedUrlParts = set(['/tag/', '/tags/','/tagged/','/author/', '/feed/', '/linked', '/category/', '/categories/','/comments', '/comment', '?like_comment', '?replytocom', '?share', '?showComment', '?showcomments', '?answertab', '?noredirect'])):
    allowedLinks = []
    linkList = [link for link in linkList if all(bannedUrlPart not in link for bannedUrlPart in bannedUrlParts)]
    for link in linkList:
        addLink = True
        for bannedUrl in bannedUrls:
            if isUrlBanned(link, bannedUrl):
                addLink = False
        if addLink == True:
            allowedLinks.append(link)
        else:
            self.logger.debug('removing banned url ' + link)
    return allowedLinks

def removeDeadLinks(linkList):
    #this function is incredibly slow, so for now I'm not actually using it but I may come back to it later
    for link in linkList:
        try:
            isValid = urlopen(link).getcode() == 200
        except:
            linkList.remove(link)
        if not isValid:
            linkList.remove(link)
    return linkList

def checkUrlInUrlList(url, masterUrlList):
    parse = urlparse(url)
    return False

def removeUrlScheme(url):
    split = url.split('://')
    return split[1]


class AlternetSpider(scrapy.Spider):
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'CONCURENT_REQUESTS': 100,
        'LOG_LEVEL': 'INFO',
        #'LOG_FILE': 'scrapy.log',
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': False,
        'DOWNLOAD_TIMEOUT': 15,
        #'DOWNLOAD_DELAY': 2,
        'AJAXCRAWL_ENABLED': True,
        'DOWNLOAD_MAXSIZE': 5000000
    }
    name = "alternet"
    
    urls = []
    f = open('urlLists/urlsToCrawl.txt', 'r')
    urls = f.read().splitlines()
    f.close()
    f = open('urlLists/masterUrlList.txt', 'r')
    urlMasterList = f.read().splitlines()
    f.close()
    urlMasterList += urls
    f = open('urlLists/bannedUrls.txt', 'r')
    bannedUrls = f.read().splitlines()
    for i in range(len(bannedUrls)):
        bannedUrls[i] = bannedUrls[i].split(' ')
    f.close()
    currentUrl = urls[0]
    HTMLParser = HTMLParser()
    '''
    In the future if crawling takes too long I can always save the webIndex and only crawl new pages-the reason why I'm commenting this out is that the occurance count will be # of word occurances * # of times the site has been crawled. It's definitely a solvable problem, but for now it's just easier to crawl the whole universe.
    One solution would be save a txt file with a list of crawled urls and don't update the webindex for sites that have already been crawled.
    try:
        with open(HTMLParser.webIndexPath, 'r') as f:
            HTMLParser.webIndex = json.load(f)
    except:
        pass
    '''
    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        self.currentUrl = removeUrlScheme(response.url)
        filename = 'crawledFiles/' + slashToPipe(self.currentUrl)
        #Final sanity check if the nextPages pruning missed something (also catches redirects to outside urls)
        if not isUrlInUniverse(self, self.currentUrl, self.urlMasterList):
            try:
                self.logger.debug('Accidental out of universe link, removing: ' + filename)
                os.remove(filename)
            except:
                self.logger.debug('Failed to remove: ' + filename)
            return None
        with open(filename, 'wb') as f:
            f.write(response.body)
            f.close()
        
        self.logger.info('Parsing %s' % response.url)

        #This prevents elements without an end tag (such as <br>) from accumulating and spilling over to the next web page
        self.HTMLParser.currentTags = []
        self.HTMLParser.wordPosition = 0
        #reset the index and path locations
        self.HTMLParser.webIndex = {}
        self.HTMLParser.pageIndex = {}
        self.HTMLParser.linkIndex = {}
        indexFilename = slashToPipe(self.currentUrl)
        self.HTMLParser.webIndexPath = 'webIndexCache/' + indexFilename + '.json'
        self.HTMLParser.pageIndexPath = 'pageIndexCache/' + indexFilename + '.json'
        self.HTMLParser.linkIndexPath = 'linkIndexCache/' + indexFilename + '.json'
        self.HTMLParser.skipDocument = False 

        indexHTML(self.HTMLParser, filename, self.HTMLParser.webIndexPath, self.currentUrl) 
                
        #delete the html file
        try: os.remove(filename)
        except: pass
        #if index html says to skip the document, end it here
        if self.HTMLParser.skipDocument:
            return None
        #gets all links from the downloaded page and deletes all the links on the outside
        nextPages = response.css('a::attr(href)').getall()
        self.logger.debug('before culling nextpages' + str(nextPages))
        #TODO: when I work on loading and saving make sure to change self.urls to be something that accesses a master list of urls, not just the urls to be crawled
        nextPages = removeOutsideLinks(self, nextPages, self.currentUrl, self.urls)
        nextPages = removeRepeatedLinks(nextPages)
        #Add to link index
        #self.HTMLParser.linkIndex[self.currentUrl] = relativeToAbsoluteUrl(self.currentUrl, nextPages)
        nextPages = relativeToAbsoluteUrl(response.url, nextPages)
        #remove self links must occur after relative to absolute because otherwise it wouldn't be able to catch things like href = '/'
        nextPages = removeSelfLinks(self, nextPages, self.currentUrl)
        nextPages = removeBannedUrls(self, nextPages, self.bannedUrls)
        nextPages = removeBadFileLinks(self, nextPages)
        #this notation is pretty crucial, i was getting all sorts of weird behavior becuase I originally was iterating over a list while removing elements from that list
        nextPages = [page for page in nextPages if isUrlInUniverse(self, page, self.urlMasterList)]
        #add to link index
        self.HTMLParser.linkIndex[self.currentUrl] = nextPages
        self.logger.debug('after culling next pages' + str(nextPages))
        #save the webIndex
        with open(self.HTMLParser.webIndexPath, 'w+') as f:
            json.dump(self.HTMLParser.webIndex, f)
            f.close()
        #save linkIndex
        with open(self.HTMLParser.linkIndexPath, 'w+') as f:
            json.dump(self.HTMLParser.linkIndex, f)
            f.close()
        #save numWordsIndex
        with open(self.HTMLParser.pageIndexPath, 'w+') as f:
            json.dump(self.HTMLParser.pageIndex, f)
            f.close()
        yield from response.follow_all(nextPages, callback=self.parse)

