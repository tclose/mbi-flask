FROM python:3.7.3-alpine3.9

LABEL maintainer="Tom Close <tom.g.close@gmail.com>"

# Add packages
RUN apk update && apk add --no-cache --virtual .build-deps \
      py3-gunicorn \
      postfix \
      ruby-dev \
      ruby \
      ruby-dev \
      libffi-dev \
      build-base \
      sqlite \
      tzdata && \
    gem install --no-document \
      listen \
      sass \
      compass \
      compass-colors && \
    apk del \
      .build-deps \
      build-base \
      libffi-dev \
      ruby-dev


# Install Python dependencies
COPY ./requirements.txt /requirements.txt
RUN pip3 install --upgrade pip && \    
    pip3 install --no-cache-dir gunicorn -r /requirements.txt

#  Set timezone
ARG TIMEZONE
RUN ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
    echo $TIMEZONE > /etc/timezone

# Configure app
ARG SECRET_KEY
ARG WTF_CSRF_SECRET_KEY
ARG MAIL_PASSWORD
ADD ./config.template config.template

# Add secrets passed in as environment variables to config.py
RUN  apk add --no-cache --virtual .build-deps gettext && \
     cat config.template | envsubst > config.py && \
     apk del .build-deps gettext


# Launch Gunicorn
EXPOSE 8000
ARG NPROCS
CMD ["/usr/local/bin/gunicorn", "-w", $NPROCS, "-b", "0.0.0.0:8000", "app:app"]
