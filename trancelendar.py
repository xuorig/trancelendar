import urllib2
from bs4 import BeautifulSoup
from dateutil import parser


import argparse
import httplib2
import os
import sys

from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools

#Google APIS Stuff
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
  scope=[
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.readonly',
    ],
    message=tools.message_if_missing(CLIENT_SECRETS))


# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

EDMCANADA_URL = 'http://www.edmcanada.com/montreal/'


def get_date_from_string(text):
    text = ' '.join(text.replace(',','').split(' ')[0:3])
    return parser.parse(text)

def get_event_strings():

    soup = BeautifulSoup(urllib2.urlopen(EDMCANADA_URL))
    urls = []

    #Get this month events
    for event_div in soup('div', {'class': 'sqs-block link-block sqs-block-link'}):
        for event in event_div.find_all('div', {'class': 'sqs-link'}):
            for event_link in event.find_all('a'):
                urls.append(event_link.text)

    #Get the other events
    for event in soup('div', {'class': 'sqs-block html-block sqs-block-html','data-block-type':'2'}):
        for link in event.find_all('a'):
            urls.append(link.text)

    return urls


def main(argv):

    flags = parser.parse_args(argv[1:])
    storage = file.Storage('sample.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(FLOW, storage, flags)

    http = httplib2.Http()
    http = credentials.authorize(http)

    service = discovery.build('calendar', 'v3', http=http)

    try:
        print "Success! Now add code here."
        calendar = service.calendars().get(calendarId=found_id).execute()
        import pdb; pdb.set_trace()
        #Check if trance calendar already exists. If it does, delete it and create a new one.



        #Create the calendar
        calendar = {
            'summary': 'trance-calendar',
            'timeZone': 'America/Montreal'
        }

        created_calendar = service.calendars().insert(body=calendar).execute()
        print('created calendar id:%s',created_calendar['id'])

        #Now we add all the found events in the calendar!
        event_strings = get_event_strings()


    except client.AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
        "the application to re-authorize")



if __name__ == '__main__':
  main(sys.argv)

