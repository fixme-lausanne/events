#!/usr/bin/env python2
# -*- coding: utf8 -*-
#from __future__ import unicode_literals

from flask import Flask, render_template, request, url_for, redirect, session
from twython import Twython
import random, sys, arrow, requests, json, re

from IPython import embed
# embed()

import gflags
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

import config as cfg

UA = 'fixme-events/0.1'
url = None
app = Flask(__name__)
if cfg.secret_key == '':
    print 'configure secret_key!'
    sys.exit(0)
app.debug = True # FIXME: remove on production
app.secret_key = cfg.secret_key

#
#    PAGES
#

@app.route('/')
def home():
    session['username'] = random.getrandbits(32)
    return render_template('form.html', data={
        'js': url_for('static', filename='main.js'),
        'css': url_for('static', filename='style.css'),
    })

@app.route('/send', methods=['POST', 'GET'])
def send():
    error = None
    services = []
    if request.method == 'POST':
        try:
            data = {
                'title': request.form['ev_title'],
                'date_from': request.form['ev_date_from'],
                'date_to': request.form['ev_date_to'],
                'time_from': request.form['ev_time_from'],
                'time_to': request.form['ev_time_to'],
                'cp': request.form['ev_cp'],
                'city': request.form['ev_city'],
                'address': request.form['ev_address'],
                'url': request.form['ev_url'],
                'free': request.form['ev_free'],
                'tags': request.form['ev_tags'],
                'description': request.form['ev_description'],
                'twitter': request.form['ev_twitter'],
                'type': request.form['ev_type'],
            }
            fserv = request.form.getlist('ev_services')
            if u'fixme' in fserv:
                services.append(send_fixme(data))
            if u'techup' in fserv:
                services.append(send_techup(data))
            if u'agendalibre' in fserv:
                services.append(send_agendalibre(data))
            if u'gcal' in fserv:
                services.append(send_gcal(data))
            if u'twitter' in fserv:
                services.append(send_twitter(data))
            if u'facebook' in fserv:
                services.append(send_facebook(data))
        except KeyError, e:
            error = e
            print e
        return render_template('send.html', data={
            'services': services,
            'error': error
        })
    return redirect('/')

#
#    SERVICES
#

# Site FIXME
def send_fixme(data):
    global url

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    desc = data['description'].split(' ')
    r = requests.post(cfg.fixme['civicrm_rest_url'], headers={'User-Agent': UA}, data={
        'json': 1,
        'sequential': 1,
        'entity': 'Event',
        'action': 'create',
        'title': data['title'],
        'event_type_id': data['type'],
        'start_date': date_from.format('YYYY-MM-DD HH:mm'),
        'end_date': date_to.format('YYYY-MM-DD HH:mm'),
        'summary': ' '.join(desc[:10]) + '...' if len(desc) > 10 else '', #it's not perfect
        'description': ' '.join(desc[10:]),
        'is_event_public': 1,
        'is_active': 1,
        'key': cfg.fixme['civicrm_site_key'],
        'api_key': cfg.fixme['civicrm_api_key'],
    })
    #embed()
    url = 'https://fixme.ch/civicrm/event/info?id=%s' % r.json['id'] if r.json !=None else ''
    return {'name': 'FIXME website', 'url': url}

# Agenda du Libre
def send_agendalibre(data):

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    if url != None:
        data['url'] = url

    r = requests.post('http://www.agendadulibre.ch/submit.php', headers={'User-Agent': UA}, data={
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
        '__event_description': data['description'],
        '__event_city': data['city'],
        '__event_region': 22,
        '__event_locality': 0, #Locale=0, Nationale=1
        '__event_url': data['url'],
        '__event_contact': 'info@fixme.ch',
        '__event_submitter': 'info@fixme.ch',
        '__event_tags': data['tags'].replace(',', ' '),
        '__event_save': 'Valider',
    })
    #embed()
    return {'name': 'Agenda du Libre', 'url': 'http://www.agendadulibre.ch'}

# TECHUP
def send_techup(data):

    #FIXME: needs twitter auth

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    if url != None:
        data['url'] = url

    # Get CSRF cook
    r = requests.get('http://techup.ch/submit', headers={'User-Agent': UA}, cookies={
            'techup': cfg.techup['techup'],
            'techupauth2': cfg.techup['techupauth2'],
        })
    token = re.findall('name="event\[_token\]" value="(\w*)"', r.content)[0]

    # Send event
    r = requests.post('http://techup.ch/submit', headers={'User-Agent': UA}, cookies={
            'techup': cfg.techup['techup'],
            'techupauth2': cfg.techup['techupauth2'],
        }, data={
        'is_free': data['free'],
        'event[_token]': token,
        'event[name]': data['title'],
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
    return {'name': 'Techup', 'url': 'http://techup.ch'}

# GOOGLE
def auth_goog(FLOW):
    FLAGS = gflags.FLAGS

    storage = Storage('google.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
      credentials = run(FLOW, storage)

    http = httplib2.Http()
    http = credentials.authorize(http)
    return http

# Calendar
def send_gcal(data):
    if url != None:
        data['url'] = url
    FLOW = OAuth2WebServerFlow(
        client_id = cfg.gcal['client_id'],
        client_secret = cfg.gcal['client_secret'],
        scope = 'https://www.googleapis.com/auth/calendar',
        user_agent = UA)
    http = auth_goog(FLOW)
    service = build('calendar', 'v3', http=http)
    post = {
      "summary": data['title'],
      "description": data['description'],
      "location": '%s, %s %s' % (data['address'], data['cp'], data['city']),
      "start": {
        "dateTime": "%sT%s:00.000+02:00" % (data['date_from'], data['time_from']),
        "timeZone": "Europe/Zurich"
      },
      "end": {
        "dateTime": "%sT%s:00.000+02:00" % (data['date_to'], data['time_to']),
        "timeZone": "Europe/Zurich"
      },
      "source": {
            "title": "Event link",
            "url": data['url'],
      },
    }

    evt = service.events()
    r = evt.insert(calendarId=cfg.gcal['calendarId'], body=post).execute()
    #embed()
    return {'name': 'Google Calendar', 'url': r['htmlLink']}

# TWITTER
def send_twitter(data):
    twitt = Twython(
        cfg.twitter['app_key'],
        cfg.twitter['app_secret'],
        cfg.twitter['access_token'],
        cfg.twitter['access_secret'],
    )
    try:
        date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
        date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')
        r=twitt.update_status(status='Event: %s, %s %s' % (
            data['title'],
            date_from.format('D MMM YYYY HH:ss'),
            data['url'],
        ))
    except Exception, e:
        return {'name': 'Twitter', 'url': '', 'error': e}
    return {'name': 'Twitter', 'url': 'https://twitter.com/_fixme/status/%s' % (r['id_str'])}

# FACEBOOK
@app.route('/fbauth')
def fbauth():
    return '<a href="https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=https://events.fixme.ch/fbauth&scope=manage_pages,publish_stream&state=%s">Click here</a>' % (\
        cfg.facebook['client_id'],
        #cfg.facebook['client_secret'],
        'abcdefghifklmnopqrstuvwxyz',
    )

def send_facebook(data):

    date_from = arrow.get('%s %s' % (str(data['date_from']), str(data['time_from'])), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (str(data['date_to']), str(data['time_to'])), 'YYYY-MM-DD HH:mm')

    if url != None:
        data['url'] = url

    r = requests.post(cfg.facebook['url'], headers={'User-Agent': UA}, data={
        'message': 'Event: %s, %s - %s' % (
            data['title'],
            date_from.format('D MMM YYYY HH:ss'),
            date_to.format('D MMM YYYY HH:ss'),
        ),
        'link': data['url'],
        'picture': 'https://fbcdn-sphotos-d-a.akamaihd.net/hphotos-ak-xfa1/t1.0-9/400419_313649045338844_1285783717_n.jpg',
        'description': data['description'],
        #'place': '194766147227135',
        'access_token': cfg.facebook['access_token'],
    })
    #embed()
    error = ''
    res = r.json()
    url_id = 'https://www.facebook.com/fixmehackerspace'
    if 'id' in res:
        url_id= 'https://www.facebook.com/fixmehackerspace/posts/%s'%r.json()['id'].split('_')[1]
    elif 'error' in res:
        error = res['error']['message']
    return {'name': 'Facebook', 'url': url_id, 'error': error}

#
#    MAIN
#

if __name__ == '__main__':
    app.run()

