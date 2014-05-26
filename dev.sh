#!/usr/bin/env bash
port=8000
python -m http.server $port || python -m SimpleHTTPServer $port
