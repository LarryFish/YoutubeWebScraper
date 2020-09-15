from urllib.request import urlopen
import json
from pprint import pprint
import httplib2
import datetime
import time
import os
import requests
from apiclient import discovery
from apiclient.discovery import build
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

#Fix issue where if no nextSearch page because not enough results it brings up error
#Properly separate code to where can do multiple pages of next results
    #Possibly pull number of results based on search query

#Designate search query phrase
queryPhrase = "Google Pixel"

def get_credentials():
    #Needed for creation of credentials with scope
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/spreadsheets'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Google Sheets API Python Quickstart'
    #User Authorization Credentials
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns: Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'sheets.googleapis.com-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def write_header():
    #Write the column names in the first row
    #Basics for Sheets API Usage
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?''version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
    #ID variable of spreadsheet to update
    spreadsheetId = "1wu5If6XRzD-Vn0nzSRpBn78kbx1CAapi24M13PXU_6Q"
    rangeName = 'Sheet1!A1:G1'
    #How input data should be interpreted
    value_input_option = 'USER_ENTERED'
    #Entry Data
    values = [["Youtuber", "ViewCount", "SubscriberCount", "VideoCount", "Date", "Time", "Timezone"]]
    body = {'values': values}
    #Request service and execute response
    request = service.spreadsheets().values().update(spreadsheetId=spreadsheetId, range=rangeName, valueInputOption=value_input_option, body=body).execute()

def write_data():
    #Count used for sheet range positioning
    count = 2
    pageToken = 0
    channels = []
    youtube = build('youtube', 'v3', developerKey='AIzaSyA6wSPqqNO9kih67gK9tuRA9_PynY77xF8')

    def initialSearch():
        search = youtube.search().list(
            part='snippet',
            maxResults=50,
            q=queryPhrase,
            type='channel').execute()
        return search

    def appendChannel():
        search = initialSearch()
        for search_result in search.get("items", []):
            if search_result["id"]["kind"] == "youtube#channel":
                channels.append("%s" % (search_result["id"]["channelId"]))
        print ('Channels:\n','\n'.join(channels),'\n')
    
    def nextSearch():
        search = initialSearch()
        nextPage = search["nextPageToken"]
        search = youtube.search().list(
            part='snippet',
            maxResults=50,
            q=queryPhrase,
            type='channel',
            pageToken=nextPage).execute()
        return search

    def nextAppendChannel():
        search = nextSearch()
        for search_result in search.get("items", []):
            if search_result["id"]["kind"] == "youtube#channel":
                channels.append("%s" % (search_result["id"]["channelId"]))
        print ('Channels:\n','\n'.join(channels),'\n')

    initialSearch()
    appendChannel()
    nextSearch()
    nextAppendChannel()

    #Uses Google Maps Geolocation API to retrieve Lat/Long based on IP address
    def get_geolocation():
        url = 'https://www.googleapis.com/geolocation/v1/geolocate?&considerIp=true&key=AIzaSyA6wSPqqNO9kih67gK9tuRA9_PynY77xF8'
        #API input in JSON format to be sent through HTTP POST request 
        payload = json.dumps({"considerIp": "true"}, sort_keys=True)
        payloadReport = requests.post(url, payload)
        response = payloadReport.text
        responseJson = json.loads(response)
        #Create List to store Lat/Long values
        latLong = []
        latitude = responseJson["location"]["lat"]
        longitude = responseJson["location"]["lng"]
        latLong.append(latitude)
        latLong.append(longitude)
        return (latLong)

    geolocation = get_geolocation()
    
    #Loop that pulls Youtube channel statistics and names for each in above list
    for channelId in channels:
        searchChannel = youtube.channels().list(part='snippet,contentDetails,statistics', id=channelId).execute()
        #Print Output into the Python Viewer
        print("________________________")
        print("Youtuber: " + searchChannel["items"][0]["snippet"]["title"])
        print("View Count: " + searchChannel["items"][0]["statistics"]["viewCount"])
        print("Subscriber Count: " + searchChannel["items"][0]["statistics"]["subscriberCount"])
        print("Video Count: " + searchChannel["items"][0]["statistics"]["videoCount"])
        #Set Variables for Write Outputs
        Youtuber = searchChannel["items"][0]["snippet"]["title"]
        ViewCount = searchChannel["items"][0]["statistics"]["viewCount"]
        SubscriberCount = searchChannel["items"][0]["statistics"]["subscriberCount"]
        VideoCount = searchChannel["items"][0]["statistics"]["videoCount"]
        base = "https://maps.googleapis.com/maps/api/timezone/json?"
        key = "&key=AIzaSyA6wSPqqNO9kih67gK9tuRA9_PynY77xF8"
        timestamp = time.time()
        params = "location={lat},{lng}&timestamp={timestamp}".format(lat=geolocation[0], lng=geolocation[1], timestamp=int(timestamp))
        url = "{base}{params}{key}".format(base=base, params=params, key=key)
        response = requests.get(url)
        string = response.text
        responseJson = json.loads(string)
        Timezone = responseJson["timeZoneName"]
        Date = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%m/%d/%y")
        Time = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%I:%M%p %Z")
        #Basics for Sheets API Usage
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?''version=v4')
        service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
        #ID variable of spreadsheet to update
        spreadsheetId = "1wu5If6XRzD-Vn0nzSRpBn78kbx1CAapi24M13PXU_6Q"
        rangeName = 'Sheet1!A%d:G%d' % (count, count)
        count += 1
        #How input data should be interpreted
        value_input_option = 'USER_ENTERED'
        #Entry Data
        values = [[Youtuber, ViewCount, SubscriberCount, VideoCount, Date, Time, Timezone]]
        body = {'values': values}
        #Request service and execute response
        request = service.spreadsheets().values().update(spreadsheetId=spreadsheetId, range=rangeName, valueInputOption=value_input_option, body=body).execute()
        time.sleep(0)

write_header()
write_data()
print("Complete")

