#!/usr/local/bin/python3

import requests # for scraping
from bs4 import BeautifulSoup # for scraping
import os # to save the result file to the system
import time # to set the delay between page scrapes
import sqlite3 # to save scraped data to sqlite file
from datetime import datetime # to timestamp things like a boss

def get_title(work):
	work_title = work.find("h4", class_="heading").a.string
	return work_title

def get_author(work):
	'''
	this field cannot be zero (author is a required field), but has a unique search string that means it cannot be included in the 'cannot_be_zero' function below, and there could be some outlying account deletions that wind up with a blank author value)

	'''
	try:
		authors = work.find("a", {"rel" : "author"}).string
	except AttributeError as e:
		return 0
	return authors

def get_fandoms(work):
	'''
	can have multiple values, but has its own search string/is not an <li> element. This requires a separate function, and so this field cannot be included in the 'has_multiple_li_tags' function below
	
	'''
	result = []
	fandoms_raw = work.find('h5', class_="fandoms heading").find_all('a')
	for item in fandoms_raw:
		result.append(item.text)
	return result

def get_reqtags(work):
	'''
	can have multiple values, but has its own search string/is not an <li> element. This requires a separate function, and so this field cannot be included in the 'has_multiple_li_tags' function below

	'''
	result = []
	reqtags_raw = work.find('ul', class_="required-tags").find_all('a')
	for item in reqtags_raw:
		result.append(item.text)
	return result

def could_be_zero(work, tagtype):
	'''
	will try to scrape the data from tags that could be zero (0) or empty ([] or null) and return a value of 0 if the field is empty 

	ELSE it will return the integer value of the field
	'''
	try:
		result = work.find('dd', class_=tagtype).text
	except AttributeError as e:
		return 0
	return result

def cannot_be_zero(work, tagtype):
	''' 
	these fields cannot be zero (they are required for each work) and so can be handled under a separate function that does not perform error checking

	is it best practice? Probably not.
	
	'''
	result = work.find('dd', class_=tagtype).text
	return result

def has_multiple_li_tags(work, tagtype):
	''' 
	these fields often contain multiple values separated by commas, and so the individual tags (which are often multiple-word strings) can be stored in lists. 

	they are cast as strings in the body of the function in order to play nice with SQLite, which does not seem to know what to do with a list that isn't explicitly cast as a string.
	
	'''
	tags = []
	tags_raw = work.find_all('li', class_=tagtype)
	for tag in tags_raw:
		tags.append(tag.text)
	return tags

def log_request(request):
	page = str(request.url)
	datestamp = str(datetime.now)
	status_code = request.status_code
	resp_time = str(request.elapsed)	
	headers = str(request.headers)
	# load the field values into a tuple for load into DB
	log_entry = (page, datestamp, status_code, resp_time, headers)
	# make the insert statement
	cur.execute('INSERT INTO r_log_spop_02 VALUES (?, ?, ?, ?, ?)', log_entry,)


def get_work_metadata(work):
	# initialize list variables for the fields that can contain multiple values
		fandoms = []
		reqtags = []
		warnings = []
		relationships = []
		characters = []
		freeforms = []

		# retrieve values for fields
		work_id = work.get('id')
		title = get_title(work)
		author = get_author(work)
		work_language = cannot_be_zero(work, 'language')
		word_count = cannot_be_zero(work, 'words')
		chapter_count = cannot_be_zero(work, 'chapters')
		collections_count = could_be_zero(work, 'collections')
		comments_count = could_be_zero(work, 'comments')
		kudos_count = could_be_zero(work, 'kudos')
		bookmarks_count = could_be_zero(work, 'bookmarks')
		hit_count = could_be_zero(work, 'hits')
		pubdate = work.find('p', class_="datetime").text
		fandoms = get_fandoms(work)
		reqtags = get_reqtags(work)
		warnings = has_multiple_li_tags(work, "warnings")
		relationships = has_multiple_li_tags(work, "relationships")
		characters = has_multiple_li_tags(work, "characters")
		freeforms = has_multiple_li_tags(work, "freeforms")

		# Create a tuple (work_row) that contains all the information for a single (1) work
		# This will be used to supply the values to the INSERT statement
		# Note that the tags that are of list() type are cast as strings here: fandoms, reqtags, warnings, relationships, characters, freeforms
		# This is in order to play nice with SQLite, which does not seem to know what to do with a list that isn't explicitly cast as a string
		work_row = (work_id, title, author, str(fandoms), str(reqtags), str(warnings), str(relationships), str(characters), str(freeforms), pubdate, work_language, word_count, chapter_count, collections_count, comments_count, bookmarks_count, kudos_count, hit_count)
		
		# Perform the INSERT statement for this work
		cur.execute('INSERT INTO spop_02 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', work_row,) # insert data for one (1) work to the database

############################
#		FUNCTION CALL      #
############################

# prompt the user for the following:

tag_id = input("Please enter the HTMLized tag ID (NOT the URL, but part of the URL) of the tag you want to scrape: ") # the tag to scrape (HTMLized)
first_page = input("Please enter the page # you'd like to start scraping on: ")
last_page = input("Please enter the page # of the last page you want to scrape: ") # the last page to scrape (page # + 1, through some Python quirk I know nothing about)

# prompt user for what to call the output file--currently TODO, is a portability issue
#fname = input("What would you like to call your results file: ") 

conn = sqlite3.connect('spop_02.sqlite') # create connection to the DB OR creates DB in current working directory if does not already exist
cur = conn.cursor() # create the cursor

cur.execute('DROP TABLE IF EXISTS spop_02')
cur.execute('DROP TABLE IF EXISTS r_log_spop_02')

# create table for scraped data
cur.execute('CREATE TABLE spop_02 (Work ID TEXT, Title TEXT, Author TEXT, Fandoms TEXT, Required Tags TEXT, Warnings TEXT, Relationships TEXT, Characters TEXT, Freeforms TEXT, Publication_Date TEXT, Language TEXT, Word Count INTEGER, Chapters INTEGER, Collections INTEGER, Comments INTEGER, Bookmarks INTEGER, Kudos INTEGER, Hits INTEGER)')

# create table for log entries
cur.execute('CREATE TABLE r_log_spop_02 (Page TEXT, Datestamp TEXT, Status Code INTEGER, Response_Time TEXT, Headers TEXT)')

''' main loop: 

loops through each work blurb group (i.e., the collection of metadata that makes up each 'work') , puts it in a tuple ('work_row') and then inserts that tuple to the database

commit() happens after every page (20 works)

there is a sleep time of 10 seconds to avoid being too annoying to the servers

'''

for i in range(1, int(last_page)):
	url = 'https://archiveofourown.org/tags/'+tag_id+'/works?page='+str(i)
	r = requests.get(url)
	src = r.text
	soup = BeautifulSoup(src, 'html.parser')
	works = soup.find_all("li", class_="work blurb group")

	# initialize list of tuples that will make up the individual rows
	log_request(r)
	one_page = []

	for work in works:
		get_work_metadata(work)
	conn.commit() # commit after each page (20 works)
	time.sleep(10) # sleep for 10 seconds between pings to the server to try not to be annoying

cur.close()