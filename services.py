##!/usr/bin/env python2
## -*- coding: utf8 -*-

'''
This file is part of FIXME Events.

FIXME Events is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

FIXME Events is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with FIXME Events. If not, see <http://www.gnu.org/licenses/>.
'''

import arrow, requests, json, re
from markdown import markdown
from twython import Twython

from IPython import embed
# embed()

import gflags
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

import config as cfg

url = None

#
#    SERVICES
#

# Site FIXME (CIVICRM)
def test_civicrm():
    try:
        r = requests.post(cfg.civicrm['rest_url'], headers={'User-Agent': cfg.user_agent}, data={
            'json': 1,
            'sequential': 1,
            'entity': 'Event',
            'action': 'getcount',
            'key': cfg.civicrm['site_key'],
            'api_key': cfg.civicrm['api_key'],
        })
        if 'result' in r.json():
            return True
        if 'is_error' in r.json() and r.json()['is_error'] == 1:
            return False
    except Exception, e:
        return e
    return r.json()

def send_civicrm(data):
    global url

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    desc = re.sub(r'(<!--.*?-->|<[^>]*>)', '', markdown(data['description'])).split(' ')
    summary = ' '.join(desc[:10]) + '...' if len(desc) > 10 else ''
    description = ' '.join(desc[10:])

    addr = 0
    if cfg.street_number in data['address']:
        addr = cfg.civicrm['default_address_id']

    r = requests.post(cfg.civicrm['rest_url'], headers={'User-Agent': cfg.user_agent}, data={
        'json': 1,
        'sequential': 1,
        'entity': 'Event',
        'action': 'create',
        'title': data['title'],
        'event_type_id': data['type'],
        'start_date': date_from.format('YYYY-MM-DD HH:mm'),
        'end_date': date_to.format('YYYY-MM-DD HH:mm'),
        'summary': summary,
        'description': description,
        'loc_block_id': addr,
        'is_event_public': 1,
        'is_active': 1,
        'key': cfg.civicrm['site_key'],
        'api_key': cfg.civicrm['api_key'],
    })
    #embed()
    error = ''
    url = ''
    if r.json() != None and 'id' in r.json():
        url = '%s?id=%s' % (cfg.civicrm['event_url'], r.json()['id'])
    else:
        error = r.content
    return {'name': cfg.civicrm['site_name'], 'url': url, 'error': error}

# Agenda du Libre
def test_agendalibre():
    r = requests.get('%s/submit.php' % cfg.agendalibre['url'], headers={'User-Agent': cfg.user_agent})
    if r.status_code == 200:
        return True
    return r.content

def send_agendalibre(data):

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')
    description = markdown(data['description'])

    if url != None:
        data['url'] = url

    r = requests.post('%s/submit.php' % cfg.agendalibre['url'], headers={'User-Agent': cfg.user_agent}, data={
        '__event_title': data['title'],
        '__event_start_day': date_from.format('DD'),
        '__event_start_month': date_from.format('MM'),
        '__event_start_year': date_from.format('YYYY'),
        '__event_start_hour': date_from.format('HH'),
        '__event_start_minute': date_from.format('mm'),
        '__event_end_day': date_to.format('DD'),
        '__event_end_month': date_to.format('MM'),
        '__event_end_year': date_to.format('YYYY'),
        '__event_end_hour': date_to.format('HH'),
        '__event_end_minute': date_to.format('mm'),
        '__event_description': description,
        '__event_city': data['city'],
        '__event_region': 22, # Vaud
        '__event_locality': 0, #Locale=0, Nationale=1
        '__event_url': data['url'],
        '__event_contact': cfg.site_email,
        '__event_submitter': cfg.site_email,
        '__event_tags': data['tags'].replace(',', ' '),
        '__event_save': 'Valider',
    })
    #embed()
    error = ''
    if r.status_code != 200:
        error = r.reason
    return {'name': 'Agenda du Libre', 'url': cfg.agendalibre['url'], 'error': error}

# TECHUP
def test_techup():
    r = requests.get('%s/submit' % cfg.techup['url'], headers={'User-Agent': cfg.user_agent}, cookies={
            'techup': cfg.techup['techup'],
            'techupauth2': cfg.techup['techupauth2'],
        })
    if r.status_code == 200 and '/user/%s' % cfg.twitter['account'] in r.content:
        return True
    return r.content

def send_techup(data):

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    if url != None:
        data['url'] = url

    # Get CSRF cook
    r = requests.get('%s/submit' % cfg.techup['url'], headers={'User-Agent': cfg.user_agent}, cookies={
            'techup': cfg.techup['techup'],
            'techupauth2': cfg.techup['techupauth2'],
        })
    token = re.findall('name="event\[_token\]" value="(\w*)"', r.content)[0]

    # Address
    geoloc = ''
    if cfg.street_number in data['address']:
        geoloc = cfg.techup['geoloc']

    # Send event
    r = requests.post('%s/submit' % cfg.techup['url'], headers={'User-Agent': cfg.user_agent}, cookies={
            'techup': cfg.techup['techup'],
            'techupauth2': cfg.techup['techupauth2'],
        }, data={
        'is_free': data['free'],
        'event[_token]': token,
        'event[name]': data['title'],
        'event[geolocation]': geoloc,
        'event[dateFrom][date][day]': date_from.format('D'),
        'event[dateFrom][date][month]': date_from.format('M'),
        'event[dateFrom][date][year]': date_from.format('YYYY'),
        'event[dateFrom][time][hour]': date_from.format('H'),
        'event[dateFrom][time][minute]': date_from.format('m'),
        'event[dateTo][date][day]': date_to.format('D'),
        'event[dateTo][date][month]': date_to.format('M'),
        'event[dateTo][date][year]': date_to.format('YYYY'),
        'event[dateTo][time][hour]': date_to.format('H'),
        'event[dateTo][time][minute]': date_to.format('m'),
        'event[location]': '%s, %s %s' % (data['address'], data['cp'], data['city']),
        'event[description]': data['description'],
        'event[link]': data['url'],
        'event[twitter]': data['twitter'],
        'event[tagsText]': data['tags'],
    })
    #embed()
    error = ''
    if r.status_code != 200:
        error = r.reason
    return {'name': 'Techup', 'url': cfg.techup['url'], 'error': error}

# GOOGLE
def get_flow():
    return OAuth2WebServerFlow(
        client_id = cfg.gcal['client_id'],
        client_secret = cfg.gcal['client_secret'],
        scope = 'https://www.googleapis.com/auth/calendar',
        redirect_uri = '%s/gcalauth' % cfg.site_url,
        access_type = 'offline',
        approval_prompt = 'force',
        user_agent = cfg.user_agent)

def auth_goog(code=None):
    FLAGS = gflags.FLAGS
    FLOW = get_flow()

    storage = Storage('google.dat')
    if code != None:
        credentials = FLOW.step2_exchange(code)
    else:
        credentials = storage.get()
    if credentials is None or credentials.invalid == True:
      credentials = run(FLOW, storage)

    http = httplib2.Http()
    http = credentials.authorize(http)
    return http

# Calendar
def test_gcal():
    http = auth_goog()
    service = build('calendar', 'v3', http=http)
    if service != None:
        return True
    return http

def send_gcal(data):
    if url != None:
        data['url'] = url
    http = auth_goog()
    service = build('calendar', 'v3', http=http)

    description = re.sub(r'(<!--.*?-->|<[^>]*>)', '', markdown(data['description']))
    post = {
      "summary": data['title'],
      "description": description,
      "location": '%s, %s %s' % (data['address'], data['cp'], data['city']),
      "start": {
        "dateTime": "%sT%s:00.000+02:00" % (data['date_from'], data['time_from']),
        "timeZone": cfg.gcal['timezone'],
      },
      "end": {
        "dateTime": "%sT%s:00.000+02:00" % (data['date_to'], data['time_to']),
        "timeZone": cfg.gcal['timezone'],
      },
      "source": {
            "title": "Event link",
            "url": data['url'],
      },
    }

    evt = service.events()
    r = evt.insert(calendarId=cfg.gcal['calendarId'], body=post).execute()
    #embed()
    error = ''
    if 'htmlLink' not in r:
        error = r
    return {'name': 'Google Calendar', 'url': r['htmlLink'], 'error': error}

# TWITTER
def test_twitter():
    twitt = Twython(
        cfg.twitter['app_key'],
        cfg.twitter['app_secret'],
        cfg.twitter['access_token'],
        cfg.twitter['access_secret'],
    )
    s = twitt.search(q='fixme')
    if s != None and s.items() > 0:
        return True
    return s

def send_twitter(data):

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    twitt = Twython(
        cfg.twitter['app_key'],
        cfg.twitter['app_secret'],
        cfg.twitter['access_token'],
        cfg.twitter['access_secret'],
    )

    try:
        r = twitt.update_status(status='Event: %s, %s %s' % (
            data['title'],
            date_from.format('D MMM YYYY HH:ss'),
            data['url'],
        ))
    except Exception, e:
        return {'name': 'Twitter', 'url': '', 'error': e}

    error = ''
    if 'id_str' not in r:
        error = r

    return {'name': 'Twitter', 'url': 'https://twitter.com/%s/status/%s' % (cfg.twitter['account'], r['id_str']), 'error': error}

# FACEBOOK
def test_facebook():
    r = requests.post(cfg.facebook['url'], headers={'User-Agent': cfg.user_agent}, data={
        'access_token': cfg.facebook['access_token'],
    })
    if r != None and r.status_code == 200:
        return True
    return r.json()['error']['message']

def send_facebook(data):

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    if url != None:
        data['url'] = url

    description = re.sub(r'(<!--.*?-->|<[^>]*>)', '', markdown(data['description']))
    r = requests.post(cfg.facebook['url'], headers={'User-Agent': cfg.user_agent}, data={
        'message': 'Event: %s, %s - %s' % (
            data['title'],
            date_from.format('D MMM YYYY HH:ss'),
            date_to.format('D MMM YYYY HH:ss'),
        ),
        'link': data['url'],
        'picture': cfg.facebook['url_pic'],
        'description': description,
        'access_token': cfg.facebook['access_token'],
    })
    #embed()
    error = ''
    res = r.json()
    url_id = cfg.facebook['url_page']
    if 'id' in res:
        url_id += '/posts/%s' % r.json()['id'].split('_')[1]
    elif 'error' in res:
        error = res['error']['message']
    return {'name': 'Facebook', 'url': url_id, 'error': error}


smap = {
    u'fixme': [send_civicrm, test_civicrm],
    u'techup': [send_techup, test_techup],
    u'agendalibre': [send_agendalibre, test_agendalibre],
    u'gcal': [send_gcal, test_gcal],
    u'twitter': [send_twitter, test_twitter],
    u'facebook': [send_facebook, test_facebook],
}
