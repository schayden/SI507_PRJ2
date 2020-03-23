#################################
##### Name: Stephen Hayden      #
##### Uniqname: schayden        #
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time
import sys

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}
api_key = secrets.MAPQUEST_API_KEY
api_secret = secrets.MAPQUEST_SECRET

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        CACHE_FILE_NAME.close()
    except:
        cache = {}
    return cache

def save_cache(cache_dict):
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILE_NAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 
def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def make_url_request_using_cache(url, cache_dict):
    if (url in cache_dict.keys()): # the url is our unique key
        print("Using cache")
        return cache_dict[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache_dict[url] = response.text
        save_cache(cache_dict)
        return cache_dict[url]



class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category="None", name="No Name", address = 'No address', zipcode = 'No zipcode', phone='No phone number'):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return (f"{self.name} ({self.category}): {self.address} {self.zipcode}")
        #`Isle Royale (National Park): Houghton, MI 49931`

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    states_dict = {}
    nps_url = 'https://www.nps.gov/index.htm'
    response = make_url_request_using_cache(nps_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    states = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')#role='menu'
    states_list = states.find_all('li', recursive = False)
    #print(states)
    for url in states_list:
        state_key = url.text.strip().lower()
        state_value = 'https://www.nps.gov'+url.a.get('href')
        states_dict[state_key] = state_value

    #for url in states_href:
        #print(url)
    #for children in states_list:
    return states_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    category = soup.find('span', class_ = "Hero-designation").text
    content_list = soup.find_all('div', class_ = 'Hero-titleContainer clearfix')[0]
    for div in soup.find_all('div', attrs={'class':'Hero-titleContainer clearfix'}):
        name = (div.find('a').contents[0])
    address = soup.find_all('div', itemprop="address")
    if soup.find('span', class_ = 'street-address') == None:
        street = "No address"
    else:
        street = soup.find('span', class_ = 'street-address').text
    locality = soup.find('span', itemprop = 'addressLocality').text
    region = soup.find('span', itemprop='addressRegion').text
    address = (locality+", "+region)
    zipcode = soup.find('span', itemprop='postalCode').text.strip()
    phone_number = soup.find('span', itemprop= 'telephone', class_ = 'tel').text.strip()
    return NationalSite(category, name, address, zipcode, phone_number)

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''

    response = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    sites_list = soup.find_all('li')
    sites_href = []
    site_links = []
    list1=[]
    return_list = []
    for div in sites_list:
        sites_href.append(div.find('h3'))
    for item in sites_href:
        if item is not None:
            list1.append(item)
    for url in list1:
        site_link = 'https://www.nps.gov'+url.a.get('href')
        site_links.append(site_link)
    for site in site_links:
        return_list.append(get_site_instance(site))
    return (return_list)




def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    params = {'key': api_key, 'origin': site_object, 'radius': 10, 'maxMatches':10, 'ambiguities': "ignore"}
    url = 'http://www.mapquestapi.com/search/v2/radius'
    #http://www.mapquestapi.com/search/v2/radius?key=KEY&maxMatches=4&origin=39.750307,-104.999472
    full_url = (f'{url}?key={api_key}&maxMatches={10}&origin={site_object}&ambiguities=ignore&outFormat=json')
    response = requests.get(url, params = params).json()
    if (full_url in CACHE_DICT.keys()): # the url is our unique key
        print("Using cache")
        return CACHE_DICT[full_url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url, params = params).json()
        CACHE_DICT[full_url] = response
        save_cache(CACHE_DICT)
        return CACHE_DICT[full_url]
    return response

if __name__ == "__main__":
    #print(get_site_instance('https://www.nps.gov/noco/index.htm').info())
    CACHE_DICT = load_cache()
    states_dict = build_state_url_dict()
    
    state_query = input('Enter a state name e.g.(Michigan, michigan) or "exit":' ).lower() #should eventually go in Main(), block out for testing purposes
    while state_query != "exit":
        while state_query not in states_dict:
            state_query = input("[Error] Enter a proper state name: ")
        state_url = states_dict[state_query]
        name_string = ("List of national sites in "+state_query)
        dashes = ('-' * len(name_string))
        #print(len(name_string))
        object_list = get_sites_for_state(state_url)
        print(f'''
        {dashes}
        List of national sites in {state_query}
        {dashes}
        ''')
        numbered_list = []
        count_print = 1
        for site in object_list:
            compound_info = ("["+(str(count_print)+"]"+ " "+site.info()))
            numbered_list.append(compound_info)
            count_print +=1
        for site in numbered_list:
            print(site)
        count_dict = {}
        count = 1
        for obj in object_list:
            count_dict[count] = obj
            count +=1
        #print(count_dict.keys())
        api_query = input("Choose the number for detail search or 'exit' or 'back': ")
        if api_query == "back":
            state_query = input('Enter a state name e.g.(Michigan, michigan) or "exit":' ).lower()
        elif api_query =="exit":
            print("Goodbye")
            sys.exit(0)
        elif api_query.isalpha():
            api_query=input("[Error] Invalid input: ")
        elif api_query.isnumeric():
            if int(api_query) not in count_dict.keys():
                api_query=input("[Error] Invalid input: ")
            else:
                int_query = int(api_query)
                #print("AAAAAAAAAAAAA")
                select_site = count_dict[int_query]
                site_address=select_site.address
                nearby_json = (get_nearby_places(site_address))#
                json_count = 0
                places = ("Places near "+select_site.name)
                api_dashes = ('-' * len(places))
                print(f'''
                {api_dashes}
                List of national sites in {select_site.name}
                {api_dashes}
                ''')
        #print(nearby_json['searchResults'][0])#dict_keys(['hostedData', 'resultsCount', 'origin', 'totalPages', 'options', 'searchResults', 'info']
                for location in nearby_json:
        #print(nearby_json['searchResults'][json_count]['fields'].keys())
                    location_name = nearby_json['searchResults'][int(json_count)]['name']
                    if 'group_sic_code_name' in nearby_json['searchResults'][int(json_count)]['fields'].keys():
                        location_category = nearby_json['searchResults'][int(json_count)]['fields']['group_sic_code_name_ext']
                    else:
                        location_category = "No Category"
                    if 'address' in nearby_json['searchResults'][int(json_count)]['fields'].keys():
                        location_add = nearby_json['searchResults'][int(json_count)]['fields']['address']
                    else:
                        location_add = 'No Address'
                    if 'city' in nearby_json['searchResults'][int(json_count)]['fields'].keys():
                        location_city = nearby_json['searchResults'][int(json_count)]['fields']['city']
                    else:
                        location_city = "No City"
                    print(f'- {location_name} ({location_category}): {location_add}, {location_city}')#
                    json_count+=1
            state_query = input('Enter a state name e.g.(Michigan, michigan) or "exit":' ).lower()
        #json_count+=1
    #print(CACHE_DICT)
    ## see if cache is working
    print("Goodbye")
    sys.exit(0)