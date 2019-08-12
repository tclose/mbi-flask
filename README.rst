MBI-Flask
=========

A collection of Flask apps to perform simple administration tasks such as
receive incidental reports or serve worklists.

The structure of the applications follows the pattern described here,
https://gist.github.com/cuibonobo/8696392

Deployment
----------

<NOTE the following instructions assume that you are in this directory>

Before installation you will need to install the dependencies in the
'requirements.txt' file. This is best done using ``pip3``::

    $ pip3 install -r web/requirements.txt

You will also need to compile the CSS from the Sass sources by::

    $ sudo apt install ruby-compass
    $ sudo gem install compas-colors
    $ pushd web/app/static/scss; compass compile; popd

You will need to create a copy of ``config-example.py`` called ``config.py``
and edit it to reflect your deployment environment

Now you can initialise the database by running `init_db.py`::

    $ python3 init_db.py


