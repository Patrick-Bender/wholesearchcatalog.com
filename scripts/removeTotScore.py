import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
pagedb = client['pageIndex']
for collection in pagedb.list_collection_names():
    x = pagedb[collection].delete_many({'tag':'totScore'})
    print('deleted ', x.deleted_count, 'from ', collection)

