def __init__():
  if name is main:
    main()

import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
import re

"""# Defining methods
building the scraping engine. 
1.   Gets each page of listings
2.   Assembles list of search results
3.   Stores each listing in "Listing" object
4.   Tabulates data from Listing objects
"""

#Listing object holds all information relevant to the post. Non normalized, Has redundancy.

class Listing:

  def __init__(self, url):
    self.url = url
    browser = start_browser()
    browser.get(url)
    self.ID = _xml_getter(url, before = "/", after=".html")[-10::]

    try:
      self.html = BeautifulSoup(browser.page_source, features='html.parser')
    except:
      try:
        time.sleep(1)
        browser.get(url)
        time.sleep(1)
        self.html=BeautifulSoup(browser.page_source)
      except:
        pass

    def parse_attributes(self):


      def get_price(self):
        try:
          price = self.html.find('span', class_='price').text
          price = re.sub(r'[^\d.]', '', str(price))
          return(int(price))
        except:
          return(None)
        

      def get_beds(self):
        housing = self.html.find("span", class_='housing')
        if housing is not None:
          beds = _xml_getter(housing.text.lower(), before=' ', after="br")
        else:
          beds = 0
        return(beds)

      def get_sqft(self):
        housing = self.html.find('span', class_='housing')
        if housing is not None:
          sqft =_xml_getter(housing.text.lower(), before=' - ', after="ft2")
          if sqft is not None:
            sqft = int(sqft)
          else: sqft = None
        else: sqft = None
        return(sqft)

      def get_park(self):
        park = _xml_getter(self.html, before='>', after="parking")
        return(park)

      def get_baths(self):
        bedbath = self.html.find('span', class_='shared-line-bubble')
        if bedbath is not None:
          baths = _xml_getter(bedbath.text.lower(), before="/ ", after='ba')
          return(baths)
        else: return None

      def get_body(self):
        body = self.html.find('section', id='postingbody')
        if body is not None:
          body = body.text
          body = body.replace("\n\nQR Code Link to This Post\n\n\n", "")
          body = body.replace("\n", " ")
          return(body)
        else: return " "

      def get_address(self):
        address = self.html.find('div', class_='mapaddress')
        if address is not None:
          location = address.text
        else: location = None
        return(location)

      def get_lat_lon(self):
        try:  
          lat = self.html.find('div', id='map').get('data-latitude')
          lon = self.html.find('div', id='map').get('data-longitude')
          lat = float(lat)
          lon = float(lon)
        except:
          lat=None
          lon=None

        return(lat, lon)

      def get_attrgroup(self):
        attrgroup = self.html.find('div', class_='mapAndAttrs')
        attrlist = ['cats are OK - purrr', 'dogs are OK - wooof', 'air conditioning', 
        'furnished', 'w/d in unit', 'laundry on site', 'laundry in bldg', 
        'no laundry on site', 'no parking', 'street parking', 'off-street parking', 
        'detached garage']
        if attrgroup is not None:
          attrgroup.find_all('p', class_='attrgroup')[1]
          attrgroup = set(attrgroup.text.split("\n"))
          attrvals = []
          for attr in attrlist:
            if attr in attrgroup:
              attrvals.append(1)
            else:
              attrvals.append(0)

          return(attrvals)
        else: return [0]*(len(attrlist))


      def get_date(self):
        return _xml_getter(self.html.find('time'), before='title="', after = '"')

      self.price = get_price(self)  
      self.beds = get_beds(self)
      self.sqft = get_sqft(self)
      self.park = get_park(self)
      self.baths = get_baths(self)
      self.body = get_body(self)
      self.address = get_address(self)
      self.lat, self.lon = get_lat_lon(self)
      self.attrgroup = get_attrgroup(self)
      self.date = get_date(self)

    parse_attributes(self)

  def get_attribute_dict(self):
    attrs = [self.url, self.price, self.beds, self.sqft, self.park, self.baths, 
     self.body, self.address, self.lat, self.lon, self.date]+self.attrgroup
    attrdict = {self.ID: attrs}
    return attrdict



def start_browser():
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  #chrome_options.add_argument('--disable-dev-shm-usage')
  browser = webdriver.Chrome('chromedriver', options=chrome_options)
  browser.set_window_size(48, 32)
  return(browser)

#utility to pull variables out of xml data using leading and following tag.
#I refuse to learn regex and this is my workaround for that.

def _xml_getter(text, before="", after=""):
  if text is not None:
    text = str(text)
    m = re.search(before+'(.+?)'+after, text)
    if m:
        found = m.group(1).strip()
        return(found)
  else: return None



#Gets all listings for a given search query.
#Pages come in batches of 120. Pass "-1" to pages for all.
def get_listings(start_url, pages=-1, cooldown=0):
    browser = start_browser()
    results = {}
    end = pages*120
    if pages == -1:
      browser.get(start_url)
      end = int(BeautifulSoup(browser.page_source).find('span', class_='totalcount').text)

    for n in range(0, end, 120):
        if n>0:
          browser.get((start_url+'&s='+str(n)))
        else:
          time.sleep(cooldown)
          browser.get(start_url)

        #Debug:
        pagestart = BeautifulSoup(browser.page_source).find('span', class_='rangeFrom').text
        pageend = BeautifulSoup(browser.page_source).find('span', class_='rangeTo').text
        print("Processing: "+pagestart+" through " + pageend)
        #####

        listings = browser.find_elements(by=By.CLASS_NAME, value='result-info')
        for l in listings:
          html = l.get_attribute('innerHTML')
          #results.update(attributes)
          url = BeautifulSoup(html, features='html.parser').a.get('href')
          results.update(Listing(url).get_attribute_dict())

    listingdf = pd.DataFrame.from_dict(results, orient='index')
    listingdf.columns = ['url', 'price', 'beds', 'sqft', 'parking', 'baths', 'descript', 'adress', 'lat', 'lon', 'date',
                         'cats are OK - purrr', 'dogs are OK - wooof', 'air conditioning',
                  'furnished', 'w/d in unit', 'laundry on site', 'laundry in bldg',
                  'no laundry on site', 'no parking', 'street parking', 'off-street parking',
                  'detached garage']
    listingdf['laundry on site'] = listingdf['laundry on site']+listingdf['laundry in bldg']
    listingdf.drop(columns='laundry in bldg', inplace = True)
    listingdf['no parking'] = listingdf['no parking']+listingdf['street parking']
    listingdf.drop(columns='street parking', inplace=True)
    listingdf['dpsf'] = 1/(listingdf['sqft']/listingdf['price'])

    return listingdf

get_listings('https://chicago.craigslist.org/search/apa', pages=1).to_csv('./listingdf.csv')