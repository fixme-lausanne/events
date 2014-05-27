#!/usr/bin/env python2

from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/send', methods=['POST'])
def send():
    services = []
    if request.method == 'POST':
        services.append(send_techup())
    return render_template('send.html', services=services)

def send_techup():
    return {'name': 'techup', 'url': 'http://google.com'}

if __name__ == '__main__':
    app.debug = True
    app.run()

