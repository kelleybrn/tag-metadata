#!/usr/local/bin/python3

import requests # for scraping
from bs4 import BeautifulSoup # for scraping
import os # to save the result file to the system
import time # to set the delay between page scrapes
import sqlite3 # to save scraped data to sqlite file

def get_author(work):
	'''
	will try to scrape the commments count field and return a value of 0 if the field is empty 

	ELSE it will return the integer value of the field
	'''
	'''
	TODO: This returns a wonky-looking stringified integer representing the total number of collections the work is in--all wrapped up in a list. Is there a way to make this less complicated?

	FIXED 5/03/2020
	'''
	try:
		authors = work.find("a", {"rel" : "author"}).string
	except AttributeError as e:
		return 0
	return authors

def could_be_zero(work, tagtype):
	try:
		result = work.find('dd', class_=tagtype).text
	except AttributeError as e:
		return 0
	return result

def cannot_be_zero(work, tagtype):
	result = work.find('dd', class_=tagtype).text
	return result

def has_multiple_li_tags(work, tagtype):
	tags = []
	tags_raw = work.find_all('li', class_=tagtype)
	for tag in tags_raw:
		tags.append(tag.text)
	return tags

# prompt the user for the following: , , and what to call the output file (without the '.csv' extension)

tag_id = input("Please enter the HTMLized tag ID (NOT the URL, but part of the URL) of the tag you want to scrape: ") # the tag to scrape (HTMLized)
last_page = input("Please enter the page # of the last page you want to scrape: ") # the last page to scrape (page # + 1, through some Python quirk I know nothing about)
#fname = input("What would you like to call your results file: ") # prompt user for what to call the output file

conn = sqlite3.connect('spop_01.sqlite') # create connection to the DB OR creates DB in current working directory if does not already exist
cur = conn.cursor() # create the cursor

cur.execute('DROP TABLE IF EXISTS scraped')

cur.execute('CREATE TABLE scraped (Work ID TEXT, Title TEXT, Author TEXT, Fandoms TEXT, Required Tags TEXT, Warnings TEXT, Relationships TEXT, Characters TEXT, Freeforms TEXT, Publication_Date TEXT, Language TEXT, Word Count INTEGER, Chapters INTEGER, Collections INTEGER, Comments INTEGER, Bookmarks INTEGER, Kudos INTEGER, Hits INTEGER)')



# now, I think, we enter the main loop

'''

LOOP LOGIC: 

For each page number, append that number to the hard-coded URL for that tag's works, and scrape the page, and do all the data dump operations you've already coded

'''

for i in range(1, int(last_page)):
	url = 'https://archiveofourown.org/tags/'+tag_id+'/works?page='+str(i)
	r = requests.get(url)
	src = r.text
	soup = BeautifulSoup(src, 'html.parser')
	works = soup.find_all("li", class_="work blurb group")

	# initialize list of tuples that will make up the individual rows
	one_page = []

	for work in works:
		# initialize list variables for the fields that can contain multiple values
		fandoms = []
		reqtags = []
		warnings = []
		relationships = []
		characters = []
		freeforms = []

		# retrieve values for fields
		work_id = work.get('id')
		title = work.find("h4", class_="heading").a.string # can't be zero but has its own search string
		author = get_author(work) # can't be zero but has its own search string
		work_language = cannot_be_zero(work, 'language')
		word_count = cannot_be_zero(work, 'words')
		chapter_count = cannot_be_zero(work, 'chapters')
		collections_count = could_be_zero(work, 'collections')
		comments_count = could_be_zero(work, 'comments')
		kudos_count = could_be_zero(work, 'kudos')
		bookmarks_count = could_be_zero(work, 'bookmarks')
		hit_count = could_be_zero(work, 'hits')
		pubdate = work.find('p', class_="datetime").text
		fandoms_raw = work.find('h5', class_="fandoms heading").find_all('a')
		for fandom in fandoms_raw:
			fandoms.append(fandom.text)
		reqtags_raw = work.find('ul', class_="required-tags").find_all('a')
		for reqtag in reqtags_raw:
			reqtags.append(reqtag.text)
		warnings = has_multiple_li_tags(work, "warnings")
		relationships = has_multiple_li_tags(work, "relationships")
		characters = has_multiple_li_tags(work, "characters")
		freeforms = has_multiple_li_tags(work, "freeforms")

		work_row = (work_id, title, author, str(fandoms), str(reqtags), str(warnings), str(relationships), str(characters), str(freeforms), pubdate, work_language, word_count, chapter_count, collections_count, comments_count, bookmarks_count, kudos_count, hit_count)
		# one_page.append(work_row)
		cur.execute('INSERT INTO scraped VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', work_row,) # insert data
	conn.commit() # commit after each page 
	time.sleep(8) # sleep for 8 seconds between pings to the server to try not to be annoying

cur.close()