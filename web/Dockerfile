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
      ruby-dev && \
    rm -rf /var/cache/apk/*

RUN ls /

# Install Python dependencies
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r /requirements.txt

#  Set timezone
ARG TIMEZONE
RUN ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
    echo $TIMEZONE > /etc/timezone

WORKDIR /app

# Configure app
ARG SECRET_KEY
ARG CSRF_SECRET_KEY
ARG MAIL_PASSWORD
ADD ./config.txt config.txt
# Add secrets to config file
RUN echo config.txt > config.py



# Launch Gunicorn
EXPOSE 8000
CMD ["/usr/local/bin/gunicorn", "-w", "4", "-b" "0.0.0.0:8000"]
