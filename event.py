#!/usr/bin/env python2

from flask import Flask, render_template, request, url_for, redirect
import requests
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
        return render_template('send.html', data={
            'services': services,
        })
    return redirect('/')

def send_techup(data):
    return {'name': 'techup', 'url': 'http://google.com'}

if __name__ == '__main__':
    app.debug = True
    app.run()

