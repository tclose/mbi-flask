FROM alpine:3.9

LABEL maintainer="Tom Close <tom.g.close@gmail.com>"

# install cron, timezone and curl
RUN apk add --update --no-cache --virtual .build-deps dcron tzdata curl gnupg && \
    apk del .build-deps

# Update the cipher algorithm used to AES256
RUN echo "cipher-algo AES256" >> /root/.gnupg/gpg.conf

#  Set timezone
ARG TIMEZONE
RUN ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
    echo $TIMEZONE > /etc/timezone

# add the backup script
COPY backup.sh /backup.sh
RUN chmod +x /backup.sh

# add the sync script
COPY sync.sh /sync.sh
RUN chmod +x /sync.sh

# add the restore script
COPY restore.sh /restore.sh
RUN chmod +x /restore.sh


# Get the time that cron job should run from the docker-compose script
ARG CRON
RUN echo "SHELL=/bin/sh" > /etc/crontab
RUN echo "PATH=$PATH" >> /etc/crontab
RUN echo "$CRON /backup.sh 2>&1 >> /log.txt && /sync.sh 2>&1 >> /log.txt" >> /etc/crontab

# Run cron.....
CMD ["crond", "-f"]
