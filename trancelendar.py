import urllib2
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
import datetime
import json

import argparse
import httplib2
import os
import sys
from pytz import timezone
import pytz

from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools

#Google APIS Stuff
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets_test.json')

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
CALENDAR_NAME = 'trance-calendar'
TIMEZONE = 'US/Eastern'


def get_date_from_string(text):
    my_time_zone = timezone(TIMEZONE)
    text = ' '.join(text.replace(',','').split(' ')[0:3])
    date_time = dateparser.parse(text)
    date_time += datetime.timedelta(hours=10)
    my_time_zone.localize(date_time)
    return date_time

def datetime2json(date):
    dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime)  or isinstance(obj, datetime.date) else None
    return json.dumps(date, default=dthandler)

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
        #Check if trance calendar already exists. If it does, delete it and create a new one.

        calendar_list = service.calendarList().list().execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] == CALENDAR_NAME:
                service.calendarList().delete(calendarId=calendar_list_entry['id']).execute()

        #Create the calendar
        calendar = {
            'summary': CALENDAR_NAME,
            'timeZone': 'America/Montreal'
        }

        created_calendar = service.calendars().insert(body=calendar).execute()
        print('created calendar id:%s' % (created_calendar['id'],))

        #Now we add all the found events in the calendar!
        event_strings = get_event_strings()

        for event in event_strings:
            date = get_date_from_string(event)
            end_date = date + datetime.timedelta(hours=4)
            end_date = end_date.isoformat()
            date = date.isoformat()

            title = event.split('-')[1]

            event = {
                     'summary': title,
                     'location': 'Somewhere',
                     'start': {
                               'dateTime': date,
                               'timeZone': TIMEZONE
                               },
                     'end': {
                             'dateTime': end_date,
                             'timeZone': TIMEZONE
                             },
            }

            created_event = service.events().insert(calendarId=created_calendar['id'], body=event).execute()
            print('Created event id: %s' % (created_event['id'],))


         print('DONE. Visit https://www.google.com/calendar/render')


    except client.AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
        "the application to re-authorize")



if __name__ == '__main__':
  main(sys.argv)

