#!/usr/bin/env python2
# -*- coding: utf8 -*-

from flask import Flask, render_template, request, url_for, redirect, session
import random

import IPython
# IPython.embed()

import gflags
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

import requests, json
import config as cfg

UA = 'events/0.1'
app = Flask(__name__)

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
    services = []
    if request.method == 'POST':
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
        }
        #services.append(send_agendalibre(data))
        #services.append(send_techup(data))
        #services.append(send_gcal(data))
        return render_template('send.html', data={
            'services': services,
        })
    return redirect('/')

#
#    SERVICES
#

# Agenda du Libre
def send_agendalibre(data):

    date_from = arrow.get('%s %s' % (data['date_from'], data['time_from']), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (data['date_to'], data['time_to']), 'YYYY-MM-DD HH:mm')

    r = requests.post('http://www.agendadulibre.org/submit.php', data={
        __event_title: data['title'],
        __event_start_day: date_from.format('DD'),
        __event_start_month: date_from.format('MM'),
        __event_start_year: date_from.format('YYYY'),
        __event_start_hour: date_from.format('HH'),
        __event_start_minute: date_from.format('mm'),
        __event_end_day: date_to.format('DD'),
        __event_end_month: date_to.format('MM'),
        __event_end_year: date_to.format('YYYY'),
        __event_end_hour: date_to.format('HH'),
        __event_end_minute: date_to.format('mm'),
        __event_description: data['description'],
        __event_city: data['city'],
        __event_region: 'Vaud',
        __event_locality: 0, #Locale=0, Nationale=1
        __event_url: data['url'],
        __event_contact: 'info@fixme.ch',
        __event_submitter: 'info@fixme.ch',
        __event_tags: data['tags'],
        __event_save: 'Valider',
    })
    #IPython.embed()
    return {'name': 'techup', 'url': 'http://google.com'}

# TECHUP
def send_techup(data):

    date_from = arrow.get('%s %s' % (data['date_from'], data['time_from']), 'YYYY-MM-DD HH:mm')
    date_to = arrow.get('%s %s' % (data['date_to'], data['time_to']), 'YYYY-MM-DD HH:mm')

    r = requests.post('http://techup.ch/submit', data={
        is_free: data['free'],
        event: {
            name: data['title'],
            dateFrom: {date: {day: date_from.format('DD')}},
            dateFrom: {date: {month: date_from.format('MM')}},
            dateFrom: {date: {year: date_from.format('YYYY')}},
            dateFrom: {date: {hour: date_from.format('HH')}},
            dateFrom: {date: {minute: date_from.format('mm')}},
            dateTo: {date: {day: date_to.format('DD')}},
            dateTo: {date: {month: date_to.format('MM')}},
            dateTo: {date: {year: date_to.format('YYYY')}},
            dateTo: {date: {hour: date_to.format('HH')}},
            dateTo: {date: {minute: date_to.format('mm')}},
            location: '%s, %s %s' % (data['address'], data['cp'], data['city']),
            description: data['description'],
            link: data['url'],
            twitter: data['twitter'],
            tagsText: data['tags'],
        }
    })
    #IPython.embed()
    return {'name': 'techup', 'url': 'http://google.com'}

# GOOGLE
def auth_goog(FLOW):
    FLAGS = gflags.FLAGS

    storage = Storage('calendar.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
      credentials = run(FLOW, storage)

    http = httplib2.Http()
    http = credentials.authorize(http)
    return http

# Calendar
def send_gcal(data):
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
      }
    }

    evt = service.events()
    r = evt.insert(calendarId=cfg.gcal['calendarId'], body=post).execute()
    #IPython.embed()
    return {'name': 'Google Calendar', 'url': r['htmlLink']}

#
#    MAIN
#

if __name__ == '__main__':
    app.debug = True
    app.secret_key = cfg.secret_key
    app.run()
    #data = {'description': u'test', 'tags': u'fixme, hackerspace', 'twitter': u'', 'time_from': u'19:00', 'free': u'yes', 'date_to': u'2014-05-30', 'time_to': u'22:00', 'title': u'Test', 'url': u'https://fixme.ch/civicrm/event/info?reset=1&id=130', 'date_from': u'2014-05-30', 'address': u'Rue de Gen\xe8ve 79, 1004 Lausanne'  }
    #r=send_gcal(data)


