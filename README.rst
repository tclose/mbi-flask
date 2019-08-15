MBI-Flask
=========

A Flask web app to handle administration tasks such as registering subjects,
receiving incidental reports from radiologists and serving DICOM worklists to
research scanners.

**NOTE that all instructions assume that you are in the repository root dir.**

Development
-----------

Before installation you will need to install the dependencies in the
'requirements.txt' file. This is best done using ``pip3``::

    $ pip3 install -r requirements.txt

You will also need to compile the CSS from the Sass sources by using the Ruby
package ``compass``::

    $ sudo gem install compass compass-colors
    $ pushd app/static/scss; compass compile; popd

You will need to create a copy of ``config-example.py`` called ``config.py``
and edit it to reflect your deployment environment

Next you can initialise the database by running `init_db.py`::

    $ python3 init_db.py

Then run the app with::

    $ FLASK_APP=app flask run

Then you can access the development site by goint to http:://127.0.0.1:5000 in
your browser


Deployment
----------

The app is designed to be deployed using Docker-Compose.

You will need to install the latest versions of

* [docker](https://www.docker.com/)
* [docker-compose](http://docs.docker.com/compose)
* [openssl](http://openssl.org)

The following ports should be open to all IPs that need to access the app

* 80 (http)
* 443 (https)

You will next need to create a '.env' file in the repostiory root with the
following variables (saved as NAME=VALUE pairs on separate lines)

* FLASK_SECRET_KEY (long arbitrary string of chars used to secure the app)
* WTF_CSRF_SECRET_KEY (long arbitrary string of chars used to secure forms)
* BACKUP_PASSPHRASE (long arbitrary string of chars used to encrypt backups)
* MAIL_USER (a gmail username/password for the app to send emails from)
* MAIL_PASSWORD (the corresponding password)
* SOURCE_XNAT_USER (User for the MBI XNAT  with 'read-all' access)
* SOURCE_XNAT_PASSWORD (password for source XNAT user)
* TARGET_XNAT_USER (User for Alfred XNAT with write access to 'MBIReporting')
* TARGET_XNAT_PASSWORD (password for target XNAT user)

You will also need to obtain a SSL certificate for your machine in order to
use https. This is typically provided by your institution or a third-party
provider (e.g. GoDaddy). You will need to provide them with a
certificate-signing-request, which can be generated using openssl::

    $ mkdir -p certs
    $ openssl req -new -newkey rsa:2048 -nodes -keyout certs/key.key -out certs/cert-sign-request.csr

This will create a SSL key in the 'certs' directory along with the signing
request which you should email to your SSL certificate provider. They will then
provide you a with a cerificate (in ASCII PEM format) you must save at
``certs/cert.crt``.

Alternatively, you can generate a "self-signed" certificate, which is not
verified by a trusted 3rd party (and so is vunerable to man-in-the-middle
attacks unless the certifcate is independently installed on client machines)::

    $ mkdir -p certs
    $ openssl req -newkey rsa:2048 -nodes -keyout certs/key.key -x509 -days 365 -out cert.crt

Once these variables and certs are in place you are ready to start using
docker-compose. To initialise the database (i.e. if not copying from a previous
server)::

    $ docker-compose run web /app/database.py init --password <password-for-manager-account>

The CSS used by the site is defined in Sass, which needs to be compiled before
you run it (otherwise the site will look pretty ugly)::

    $ docker-compose run web /compile-sass.sh

After that the you should be able to bring up the app by running::

    $ docker-compose up -d

Then you can access the site by navigating to the server domain name or IP in
your browser.
