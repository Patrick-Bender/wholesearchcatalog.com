import networkx as nx
import pymongo
import time
import logging

def pageLinksDictToGraphEdges(myDict):
    myList = []
    for key in myDict:
        for endLink in myDict[key]:
            myList.append((key, endLink))
    return myList

def sliceDictionary(myDict, myList):
    return dict([(key,myDict[key]) for key in myDict if key in myList])

def pageRank(client):

    pagedb = client['pageIndex']

    pages = list(pagedb.list_collection_names())
    pageLinks = {}
    for page in pages:
        try:pageLinks[page] = pagedb[page].find_one({'tag': 'links'})['values']
        except KeyboardInterrupt: exit()
        except Exception as error: 
            logging.warning('pageranker could not find links for a page', str(page))
            continue
    logging.info('page ranker completed loading links')
    G = nx.DiGraph()
    G.add_nodes_from(pages)
    #for node in nx.nodes(G):
        #print(node, type(node))
    #print(pageLinksDictToGraphEdges(pageLinks))
    G.add_edges_from(pageLinksDictToGraphEdges(pageLinks))

    pageRank = nx.pagerank(G)
    for page in pageRank:
        try: 
            if len(bytes(page,'ascii'))>117:continue
        except: continue
        #print(page)
        #print('before', list(pagedb[page].find()))
        try:pagedb[page].replace_one({'tag': 'pageRank'}, {'tag': 'pageRank', 'values':pageRank[page], 'lastUpdated': time.time()}, upsert = True)
        except KeyboardInterrupt: exit()
        except Exception as error: 
            logging.warning('could not add pagerank score to a collection', error, str(page), str(pageRank[page]))
            continue
        #print('after', list(pagedb[page].find()))
    logging.info('page ranker completed writing to database')

format = '%(asctime)s: %(message)s'
logging.basicConfig(format=format, level=logging.INFO, datefmt='%H:%M:%S')

client = pymongo.MongoClient('mongodb://localhost:27017/')
pageRank(client)
