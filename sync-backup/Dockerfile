FROM alpine:3.9

LABEL maintainer="Tom Close <tom.g.close@gmail.com>"

#install postgres client
RUN apk update \
 && apk add --no-cache --virtual .build-deps \
 dcron postgresql-client

# disable default crontab
COPY crontab /etc/crontab
RUN mkdir -p /etc/cron.d/

# add the backup script
COPY backup.sh /backup.sh
RUN chmod +x /backup.sh

# create backup-cron file...
RUN echo "$SETUP_CRON root /backup.sh > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/cron.d/backup-cron
RUN chmod 0644 /etc/cron.d/backup-cron

# Run cron.....
CMD ["crond", "-f"]
