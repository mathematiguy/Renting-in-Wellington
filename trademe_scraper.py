'''This code scrapes trademe for Wellington rental data'''

from bs4 import BeautifulSoup
import re

def read_url(url):
	# This reads in a url and returns a BeautifulSoup object. 
	# It also catches errors if something goes wrong
	from urllib2 import urlopen
	from urllib2 import HTTPError
	from time import sleep
	print("Reading: %s" %url)

	# sleep 1 second
	# sleep(1)
	try:
	    html = urlopen(url)
	except HTTPError as e:
	    print(e)
	    return None
	try:
	    soup = BeautifulSoup(html.read(), "lxml")
	except AttributeError as e:
	    print(e)
	    return None
	return soup

def get_next_url(soup):
    domain = 'http://www.trademe.co.nz'
    tags = soup.findAll("a", {"href" : re.compile("/browse/.+")})
    next_link = [tag.get("href") for tag in tags if 'next' in tag.get_text().lower()]
    try:
        return domain + next_link[0]
    except IndexError:
        return ""

# Read the trademe wellington rental data
# Here is where we will begin scraping
#next_url = "http://www.trademe.co.nz/Browse/CategoryAttributeSearchResults.aspx?search=1&cid=5748&sidebar=1&132=FLAT&134=&216=0&216=0&217=0&217=0&153=&122=0&122=0&123=0&123=0&59=0&59=0&178=0&178=0&sidebarSearch_keypresses=0&sidebarSearch_suggested=0"
next_url = "http://www.trademe.co.nz/browse/categoryattributesearchresults.aspx?134=15&136=&153=&132=FLAT&59=0&59=35000&122=0&122=0&29=&123=0&123=0&search=1&sidebar=1&cid=5748&rptpath=350-5748-"
#next_url = "http://www.trademe.co.nz/browse/categoryattributesearchresults.aspx?134=15&136=&153=&132=FLAT&59=0&59=0&122=0&122=0&29=&123=0&123=0&search=1&sidebar=1&cid=5748&rptpath=350-5748-"
gal_cards = []
while next_url != "":
	# Extract the cards for each property and append these to a list
	page_soup = read_url(next_url)
	gal_cards += page_soup.findAll("div", {"id" : re.compile("GalleryView_\d+_GC")})
	next_url = get_next_url(page_soup)

# Create list of all rentals. Each rental will be stored as a dictionary
rentals = []
for gal_card in gal_cards:
	rental = {}
	
	# Get title and link
	title_tag = gal_card.find("a",
	              {"class" : "dotted", 
	               "href" : re.compile("/property/residential-property-to-rent/auction-\d+.htm")
	               })
	rental['title'] = title_tag.get_text()
	rental['link'] = "http://www.trademe.co.nz" + title_tag.get("href")

	# print progress
	print("Reading: %s" %rental['title'])

	# Get location
	loc_tag = gal_card.find("div", 
							{"class" : "property-card-subtitle"})
	rental['location'] = loc_tag.get_text()

	# Get price
	price_tag = gal_card.find("div", 
							  {"class" : "property-card-price"})
	rental['price'] = price_tag.get_text()

	# Get availabile date
	avail_tag = gal_card.find("div", {"class" : "property-card-available"})
	rental['available_date'] = avail_tag.get_text()

	# Get bedrooms
	bedrm_tag = gal_card.find("span", {"id" : re.compile("GalleryView_\d+_gPBed")})
	rental['bedrooms'] = bedrm_tag.get_text()

	bathrm_tag = gal_card.find("span", {"id" : re.compile("GalleryView_\d+_gPBath")})
	rental['bathrooms'] = bathrm_tag.get_text()

	listdate_tag = gal_card.find("span", {"class" : "property-card-listed-date"})
	rental['listdate'] = listdate_tag.get_text()

	contact_tag = gal_card.find("span", {"id" : re.compile("GalleryView_\d+_agentName")})
	rental['contact'] = contact_tag.get_text()

	# Now we dive deeper to extract more detailed data
	detail_soup = read_url(rental['link'])

	expire_text = "Sorry, this classified has expired."
	if expire_text in detail_soup.get_text():
		print("Listing expired.")
		continue

	def strip_tags(tag):
		'''This removes the tags from a soup of text'''
		text = str(tag)
		text = re.split('<[\w\s="]+>|</\w+>|\r|\n', text)
		text = ' '.join(text)
		# implement line breaks
		text = re.split("<br/>", text)
		text = '\n'.join(text)

		text = re.split(r"\\x\w\w", text)
		text = ' '.join(text)
		return text.strip()

	table_tag = detail_soup.find("table", {"id" : "ListingAttributes"})
	rental['table'] = {strip_tags(tag.find("th")):  \
					   strip_tags(tag.find("td"))   \
					   for tag in table_tag.findAll("tr")}

	desc_tag = detail_soup.find("div", 
							  {"id" : 
							   "ListingDescription_ListingDescription"})
	rental['description'] = desc_tag.get_text().strip()

	page_view_tag = detail_soup.find("div", 
								  {"id" : 
								   'DetailsFooter_PageViewsPanel'})
	rental['page_views'] = ''.join([tag.get("alt") for tag in page_view_tag.findAll("img")])

	rentals.append(rental)

# Save results_dict to .json file
from datetime import date
import pickle
rental_file_name = 'rentals_' + date.today().strftime("%d-%m-%Y") + ".pkl"
print("Saving results to %s..." %rental_file_name)
with open(rental_file_name, 'w') as f:
    pickle.dump(rentals, f)
print("Saved!")