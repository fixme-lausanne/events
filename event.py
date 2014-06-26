#!/usr/bin/env python2
# -*- coding: utf8 -*-
#from __future__ import unicode_literals

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

from flask import Flask, render_template, request, url_for, redirect, session
import random, sys
from services import *
import config as cfg

from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

from IPython import embed
# embed()

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

@app.route('/fbauth')
def fbauth():
    if 'code' in request.args and request.args['state'] == cfg.facebook['state']:
        return 'Got the code=%s' % request.args['code']
    else:
        return '<a href="%s?client_id=%s&redirect_uri=%s/fbauth&scope=manage_pages,publish_stream&state=%s">Click here</a>' % (\
            cfg.facebook['oauth'],
            cfg.facebook['client_id'],
            cfg.site_url,
            cfg.facebook['state'],
        )

@app.route('/gcalauth')
def gcalauth():
    FLOW = OAuth2WebServerFlow(
        client_id = cfg.gcal['client_id'],
        client_secret = cfg.gcal['client_secret'],
        scope = 'https://www.googleapis.com/auth/calendar',
        redirect_uri = '%s/gcalauth' % cfg.site_url,
        user_agent = cfg.user_agent)
    if 'code' in request.args:
        code = request.args['code']
        try:
            credentials = FLOW.step2_exchange(code)
            http = auth_goog(FLOW, code)
            #embed()
            service = build('calendar', 'v3', http=http)
        except Exception, e:
            return e
        return 'OK ' + request.args['code']
    elif 'error' in request.args:
        return request.args['error']
    else:
        url_redir = FLOW.step1_get_authorize_url()
        return redirect(url_redir)

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
                services.append(send_civicrm(data))
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
#    MAIN
#

if __name__ == '__main__':
    app.run()

