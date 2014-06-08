#!/usr/bin/env python2
# -*- coding: utf8 -*-
#from __future__ import unicode_literals

from flask import Flask, render_template, request, url_for, redirect, session
import random, sys
from services import *
import config as cfg

from IPython import embed
# embed()

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

@app.route('/fbauth')
def fbauth():
    if 'code' in request.args:
        return 'Got the code=%s' % request.args['code']
    else:
        return '<a href="https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=https://events.fixme.ch/fbauth&scope=manage_pages,publish_stream&state=%s">Click here</a>' % (\
            cfg.facebook['client_id'],
            'abcdefghifklmnopqrstuvwxyz',
        )

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
#    MAIN
#

if __name__ == '__main__':
    app.run()

