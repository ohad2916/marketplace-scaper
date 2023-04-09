import json
import math
from bs4 import BeautifulSoup
import requests
import re
import os
from collections import OrderedDict

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0'}
website_search_url = 'https://www.ebay.com/sch/i.html?_nkw='  # Replace with search url of website
item_name = 'rolex'  # Replace with search term
number_of_listings = 20  # Replace as needed
listings_per_page = 60

# Use the marketplace's search URL to retrieve a set of item-list pages' URLs known also as feed pages.
print("Getting feed-page urls...")
number_of_feed_pages_to_scrap = math.ceil(number_of_listings / listings_per_page)
feed_page_urls = OrderedDict()
current_page_url = (website_search_url + item_name)
while len(feed_page_urls) < number_of_feed_pages_to_scrap:
    feed_page_text = requests.get(current_page_url, headers=headers).text
    soup = BeautifulSoup(feed_page_text, 'lxml')
    # Replace according to the relevant website.
    new_pages_list = [feed_page_link['href'] for feed_page_link in soup.find_all('a', class_='pagination__item')]
    feed_page_urls.update(OrderedDict.fromkeys(new_pages_list))     # using OrderedDict as an Ordered-Set.
    current_page_url = new_pages_list[-1]

# Scrap each feed page to retrieve a list of items URLs
print("Getting item urls...")
item_urls = []
for feed_page_link in list(feed_page_urls.keys())[:number_of_feed_pages_to_scrap]:
    feed_page_text = requests.get(feed_page_link, headers=headers).text
    soup = BeautifulSoup(feed_page_text, 'lxml')
    # Replace according to the relevant website, [1:] is ebay specific.
    new_item_list = [web_link['href'] for web_link in soup.find_all('a', class_='s-item__link')][1:]
    item_urls.extend(new_item_list)

#   Make folder to dump data in
folder_path = r'product_data'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

print(f"Got {len(item_urls)} Product links!, scraping {min(number_of_listings, len(item_urls))}:")
# Scrap each product for its title, description, price and image path.
# Replace every query in 'product info' according to the specific website configurations.
for item_link in item_urls[:min(number_of_listings, len(item_urls))]:
    soup = BeautifulSoup(requests.get(item_link, headers=headers).text, 'lxml')
    product_info = {'title': soup.find('h1', class_="x-item-title__mainTitle").text.strip(),
                    'description': soup.find('iframe', {'title': 'Seller\'s description of item'})['src'],
                    'price': soup.find('span', {'itemprop': 'price'}).text.strip(),
                    'image_path': re.findall(r'(https?://\S+)', soup.find('script', {'type': 'text/javascript'}).text)[
                        0].replace('";', '')}
    product_id = item_link.split('/')[-1].split('?')[0]  # Extract product ID from item URL, may vary.
    marketplace_name = website_search_url.split('//')[1].split('.')[1]  # Extract marketplace name from search URL, may vary.
    file_name = f'{marketplace_name}_{product_id}.json'
    with open(folder_path + '\\' + file_name, 'w') as file:
        json.dump(product_info, file)
    print(f'--Scraped PRODUCT ID:{product_id}')
