#!/usr/bin/env python2

from flask import Flask, render_template, request, url_for, redirect

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

@app.route('/')
def home():
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
            'address': request.form['ev_address'],
            'url': request.form['ev_url'],
            'free': request.form['ev_free'],
            'tags': request.form['ev_tags'],
            'description': request.form['ev_description'],
            'twitter': request.form['ev_twitter'],
        }
        services.append(send_techup(data))
        services.append(send_gcal(data))
        return render_template('send.html', data={
            'services': services,
        })
    return redirect('/')

def send_techup(data):
    return {'name': 'techup', 'url': 'http://google.com'}

def auth_goog(FLOW):
    FLAGS = gflags.FLAGS

    storage = Storage('calendar.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
      credentials = run(FLOW, storage)

    http = httplib2.Http()
    http = credentials.authorize(http)
    return http

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
      "location": data['address'],
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
    return r

if __name__ == '__main__':
    app.debug = True
    app.run()
    #data = {'description': u'test', 'tags': u'fixme, hackerspace', 'twitter': u'', 'time_from': u'19:00', 'free': u'yes', 'date_to': u'2014-05-30', 'time_to': u'22:00', 'title': u'Test', 'url': u'https://fixme.ch/civicrm/event/info?reset=1&id=130', 'date_from': u'2014-05-30', 'address': u'Rue de Gen\xe8ve 79, 1004 Lausanne'  }
    #r=send_gcal(data)


