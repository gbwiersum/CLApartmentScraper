import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import time
import datetime
import numpy as np
import pandas as pd
import re
import requests
import json

global START
global COOLDOWN

# Using the requests library instead of selenium because it's much much faster.

def get_price(html):
    price = html.find('span', class_='price').text
    price = re.sub("\D", "", price)
    price = int(price)
    return price

def get_beds(html):
    housing = html.find('span', class_='housing')
    if housing is not None:
        beds = re.search(r'[$\d.]', housing)[0]
    else: beds = 0
    return(beds)

def get_sqft(html):
    sqft = None
    housing = html.find('span', class_='housing')
    if housing is not None:
        r = re.search("\d{2,6}ft", housing.text)
        if r:
            r = re.sub("\D", "", r.group(0))
            sqft = int(r)
        return sqft
    else: 
        return None

def get_park(html):
    park = None
    for n in html.find_all('span', class_='valu'):
        r = re.search(".*parking.*",n.text)
        if r:
            park = r.group(0)
    return(park)

def get_body(html):
    body = html.find('section', id='postingbody').text
    body = re.sub("\n\nQR(.*?)\n\n", "", body)
    return(body)

def get_address(html):
    address = html.find('div', class_='mapaddress')
    if address is not None:
        location = address.text
    else: location = None
    return(location)

def get_lat_lon(html):
    try:
        lat = html.find('div', id='map').get('data-latitude')
        lon = html.find('div', id='map').get('data-longitude')
    except:
        lat=None
        lon=None

    return(lat, lon)

def get_dog(attrgroup):
    r = re.compile('.*dogs.*')
    dog = list(filter(r.match, attrgroup))
    if len(dog)>0:
        return True
    else:
        return False

def get_cat(attrgroup):
    cat = False
    for n in attrgroup:
        r = re.search(".*cats.*", n)
        if r:
            return True
            break
    return False

def get_laundry(html):
    laundry = None
    for n in html.find_all('span', class_='valu'):
        if ("w/d" in n.text) | ("laundry" in n.text):
            laundry =(n.text)
            break
    return laundry

def get_date(html):
    date = html.find("time", class_="date timeago").text.strip()
    return date

def get_thumbs(html):
    nails = html.find('div', id='thumbs')
    thumbs = []
    if nails is not None:
        thumbs = [a.get('href') for a in nails.find_all('a')]
    return thumbs


class Listing:

    def __init__(self, url):

        self.url = url
        html = BeautifulSoup(requests.get(url).content)

        # much of the key info is gettable from a json object included in the response:
        jcard = json.loads(html.find('script', id='ld_posting_data').text)
        if "numberOfBedrooms" in jcard.keys():
                self.beds = jcard["numberOfBedrooms"]
        else:
                self.beds = 0
        if "numberOfBathroomsTotal" in jcard.keys():
                self.baths = jcard["numberOfBathroomsTotal"]
        else:
                self.baths = 0

        self.lat, self.lon = (jcard['latitude'], jcard["longitude"])

        if "petsAllowed" in jcard.keys():
                self.pet = jcard["petsAllowed"]
        else:
                self.pet=None

        #There's a collection of attributes called "attrgroup" that contains a good number of features.
        #I'm just using it as a string and searching for the keywords.
        attrgroup = [attr.text.strip() for attr in html.find_all('div', class_="attr")]
        self.cat = get_cat(attrgroup)
        self.dog = get_dog(attrgroup)

        #Getting links to thumbnail pictures:
        self.thumbs = get_thumbs(html)

        self.price = get_price(html)
        self.sqft = get_sqft(html)
        self.park = get_park(html)
        self.body = get_body(html)
        self.address = get_address(html)
        self.date = get_date(html)
        self.laundry = get_laundry(html)
        
        
        uid = re.search("/(\d{10}).html", listings[:,0][5])
        self.ID = re.sub("\D", "", uid.group(0))

    def get_attributes(self):
            attrdict = {"ID":self.ID,
                "URL":self.url,
                "Price":self.price,
                "Beds":self.beds,
                "Sqft":self.sqft,
                "Park":self.park,
                "Baths":self.baths,
                "Body":self.body,
                "Addr":self.address,
                "Lat":self.lat,
                "Lon":self.lon,
                "Date":self.date,
                "Cat": self.cat,
                "Dog": self.dog,
                "WD":self.laundry}
            return attrdict
    

def parse_listing(url):
    global errors
    errors = []
    try:
        x = Listing(url)
        out = x.get_attributes()
        time.sleep(COOLDOWN)
        return out
    except:
        errors.append(url)


def get_listings(START, COOLDOWN=1):

    response = requests.get(START)
    soup = BeautifulSoup(response.text)
    
    listings = []
    for l in soup.find_all('li')[1::]:
        url = l.a.get('href')
        title = l.find('div', 'title').text
        price = l.find('div', 'price').text
        price = re.sub(r'[^\d.]', '', str(price))
        price = int(price)
    
        listings.append([url, title, price])
    
    listings = np.array(listings)
    
    print("Links found:")
    print(len(listings))

    df = pd.DataFrame(listings, columns=["URL", "Header", 'Price'])
    df = pd.DataFrame.from_records(df["URL"].map(parse_listing))
    return df