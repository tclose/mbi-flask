FROM alpine:3.7

LABEL maintainer="Tom Close <tom.g.close@gmail.com>"

# Expose Gunicorn port
EXPOSE 8000

RUN apk add --no-cache --virtual .build-deps \
    postfix python3-pip ruby-compass sqlite3 && \
    apk del .build-deps

# Set timezone
RUN apk update && apk add --no-cache --virtual .build-deps tzdata && \
    ln -snf /usr/share/zoneinfo/Australia/Melbourne /etc/localtime && \
    echo Australia/Melbourne > /etc/timezone && \
    apk del .build-deps
ENV TZ Australia/Melbourne

WORKDIR /app

# Configure app
ARG SECRET_KEY
ARG CSRF_SECRET_KEY
ARG MAIL_PASSWORD
ADD ./config.txt config.txt
# Add secrets to config file
RUN config.py < config.txt

# Install Python dependencies
RUN pip3 install gunicorn -r requirements.txt

# Launch Gunicorn
CMD ["/usr/local/bin/gunicorn", "-w", "4", "-b" "0.0.0.0:8000"]
