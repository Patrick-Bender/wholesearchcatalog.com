import networkx as nx
import matplotlib.pyplot as plt
import json

def pageLinksDictToGraphEdges(myDict):
    myList = []
    for key in myDict:
        for endLink in myDict[key]:
            myList.append((key, endLink))
    return myList

def sliceDictionary(myDict, myList):
    return dict([(key,myDict[key]) for key in myDict if key in myList])

G = nx.DiGraph()
with open('linkIndex.json') as f:
    linkData = json.load(f)

pages = list(linkData.keys())
pageLinks = linkData

G.add_nodes_from(pages)
#for node in nx.nodes(G):
    #print(node, type(node))
#print(pageLinksDictToGraphEdges(pageLinks))
G.add_edges_from(pageLinksDictToGraphEdges(pageLinks))

pageRank = nx.pagerank(G)

pageRankFile = json.dumps(pageRank)
saveFile = open('pageRank.json', 'w')
saveFile.write(pageRankFile)
saveFile.close()

topRank = 0
topPage = ''
for page in pages:
    if pageRank[page] > topRank:
        topRank = pageRank[page]
        topPage = page

print(topPage, topRank)

#nx.draw(G)
#plt.show()
