MBI-Flask
=========

A collection of Flask apps to perform simple administration tasks such as
receive incidental reports or serve worklists.

The structure of the applications follows the pattern described here,
https://gist.github.com/cuibonobo/8696392

Deployment
----------

<NOTE all the following instructions assume that you have cd'd to this directory>

Before installation you will need to install the dependencies in the 'requirements.txt'
file. This is best done using `pip3`::

    $ pip3 install -r requirements.txt

You will also need to compile the CSS from the Sass sources by::

    $ sudo apt install ruby-compass
    $ sudo gem install compas-colors
    $ pushd app/static/scss; compass compile; popd

You can deploy the app using a number of `options <https://flask.palletsprojects.com/en/1.1.x/deploying/>`_,
the easiest of which is using `gunicorn`::

    $ sudo apt install gunicorn
    $ gunicorn -w 4 app:app
