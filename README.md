# wholesearchcatalog.com

Interesting code:

-flaskapp/flaskapp/search.py : Includes the functions that score pages for a given query based on how frequent a word appears and what HTML tags are associated with that word

-webCrawler/webCrawler/alternet\_spider.py : The crawler for downloading all thepages on a given domain

-webCrawler/indexer.py : Parses HTML pages to store which words have which HTML tag

-webCrawler/merger.py : Uploads the parsed HTML to the mongodb server. Includes both the page index (url -> keyword) and the web index (keyword -> url)

Folder Descriptions:

-Apache2: The apache configuration for the web server interface gateway for flask

-Flaskapp: All the front end code + the search functionality

-webCrawler: Code to crawl and download the HTML pages
