#!/usr/local/bin/python3

import requests # for scraping
from bs4 import BeautifulSoup # for scraping
import os # to save the result file to the system
import csv # to save the result file to the system
import time # to set the delay between page scrapes
# import sqlite3 # to save scraped data to sqlite file

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


def get_collections(work):
	'''
	will try to scrape the commments count field and return a value of 0 if the field is empty 

	ELSE it will return the integer value of the field
	'''
	'''
	TODO: This returns a wonky-looking stringified integer representing the total number of collections the work is in--all wrapped up in a list. Is there a way to make this less complicated?

	FIXED 5/03/2020
	'''
	try:
		collections = work.find('dd', class_="collections").text
	except AttributeError as e:
		return 0
	return collections


def get_comments(work):
	'''
	will try to scrape the commments count field and return a value of 0 if the field is empty 

	ELSE it will return the integer value of the field
	
	'''
	try:
		comments = work.find('dd', class_="comments").text
	except AttributeError as e:
		return 0
	return comments


def get_kudos(work):
	'''
	will try to scrape the commments count field and return a value of 0 if the field is empty 

	ELSE it will return the integer value of the field
	
	'''
	try:
		kudos = work.find('dd', class_="kudos").text
	except AttributeError as e:
		return 0
	return kudos


def get_bookmarks(work):
	'''
	will try to scrape the commments count field and return a value of 0 if the field is empty 

	ELSE it will return the integer value of the field
	
	'''
	try:
		bookmarks = work.find('dd', class_="bookmarks").text
	except AttributeError as e:
		return 0
	return bookmarks


def get_hits(work):
	'''
	will try to scrape the commments count field and return a value of 0 if the field is empty 

	ELSE it will return the integer value of the field
	
	'''
	try:
		hits = work.find('dd', class_="hits").text
	except AttributeError as e:
		return 0
	return hits

# prompt the user for the tag to scrape (HTMLized), the last page to scrape (page # + 1, through some Python quirk I know nothing about), and what to call the output file (without the '.csv' extension)

# prompt the user of the script to input the page # of the very last page they want to scrape--i.e., how far they want to go into the tag
# note that because Python defaults to a zero-index, you need to give one more page than the Archive actually lists
# WHATEVER PAGE YOU WANT TO END ON, ADD 1 TO THAT NUMBER, BECAUSE PYTHON WILL SHORT YOU ONE IF YOU DON'T
tag_id = input("Please enter the HTMLized tag ID (NOT the URL, but part of the URL) of the tag you want to scrape: ")
last_page = input("Please enter the page # of the last page you want to scrape: ")
fname = input("What would you like to call your filename plese: ")

# using the last_page value provided by the user, create a range between [1 ... last_page]
# p_range = [1 ... last_page]

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

	headers = ['Work ID', 'Title', 'Author', 'Fandoms', 'Required Tags', 'Warnings', 'Relationships', 'Characters', 'Freeforms', 'Publication Date', 'Language', 'Word Count', 'Chapters', 'Collections', 'Comments', 'Kudos', 'Hits']

	with open(fname+'.csv','a') as csvWriter:
		writer = csv.writer(csvWriter)
		writer.writerow(headers)
		for work in works:
			fandoms = []
			reqtags = []
			warnings = []
			relationships = []
			characters = []
			freeforms = []
			work_id = work.get('id')
			title = work.find("h4", class_="heading").a.string
			author = get_author(work)
			language = work.find('dd', class_="language").text
			words = work.find('dd', class_="words").text
			chapters = work.find('dd', class_="chapters").text
			collections = get_collections(work)
			comments = get_comments(work)
			kudos = get_kudos(work)
			bookmarks = get_bookmarks(work)
			hits = get_hits(work)
			pubdate = work.find('p', class_="datetime").text
			fandoms_raw = work.find('h5', class_="fandoms heading").find_all('a')
			for fandom in fandoms_raw:
				fandoms.append(fandom.text)
			reqtags_raw = work.find('ul', class_="required-tags").find_all('a')
			for reqtag in reqtags_raw:
				reqtags.append(reqtag.text)
			warnings_raw = work.find_all('li', class_="warnings")
			for warning in warnings_raw:
				warnings.append(warning.text)
			relationships_raw = work.find_all('li', class_="relationships")
			for relationship in relationships_raw:
				relationships.append(relationship.text)
			characters_raw = work.find_all('li', class_="characters")
			for character in characters_raw:
				characters.append(character.text)
			freeforms_raw = work.find_all('li', class_="freeforms")
			for freeform in freeforms_raw:
					freeforms.append(freeform.text)
			row = [work_id] + [title] + [author] + [fandoms] + [reqtags] + [warnings] + [relationships] + [characters] + [freeforms] + [pubdate] + [language] + [words] + [chapters] + [collections] + [comments] + [kudos] + [hits]
			writer.writerow(row)
	time.sleep(10) # sleep for 10 seconds between pings to the server to try not to be a dick