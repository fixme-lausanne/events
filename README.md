Events
======

Publish FIXME events on all the platforms

Installation
------------

* FIXME: There's still some hardcoded values in events.py preventing reuse as is

* Install the latest stable flask and dependencies

    ```
apt-get install python-pip python-httplib2
pip install flask requests google-api-python-client \
           oauth2client python-gflags arrow twython \
           markdown
    ```

* Create config.py and fill the empty fields

    ```cp config.py-example config.py```

* Apache example configuration for WSGI in /etc/apache2/sites-available/20_events

    ```
<VirtualHost *:80>
    ServerName events.fixme.ch
    ServerSignature Off
    CustomLog /var/www/events/logs/access.log combined
    ErrorLog /var/www/events/logs/error.log
    DocumentRoot /var/www/events/htdocs

    <Directory /var/www/events/htdocs>
        AllowOverride None
        Options -Indexes
    </Directory>

    <Files *.pyc>
        deny from all
    </Files>

    WSGIProcessGroup events.fixme.ch
    WSGIScriptAlias / /var/www/events/htdocs/app.wsgi
    WSGIDaemonProcess events.fixme.ch user=www-data group=www-data threads=50
</VirtualHost>
    ```

Screenshot
----------

![form](./screenshot.png)

License
-------

```
Copyright (C) 2014 Jean-Baptiste Aubort <rorist@0xcafe.ch>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or any later
version. This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
Public License for more details. You should have received a copy of the
GNU General Public License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
```

See gpl-3.0.txt

