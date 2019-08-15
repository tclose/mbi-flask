FROM alpine:3.9

LABEL maintainer="Tom Close <tom.g.close@gmail.com>"

#  Set timezone
ARG TIMEZONE
RUN apk add --update --no-cache --virtual .build-deps tzdata && \
    cp /usr/share/zoneinfo/$TIMEZONE /etc/localtime && \
    echo $TIMEZONE > /etc/timezone && \
    apk del .build-deps

# install cron, gpg and curl
RUN apk add --no-cache dcron curl gnupg bash

# Update the cipher algorithm used to AES256
RUN gpg --list-keys
RUN echo "cipher-algo AES256" >> /root/.gnupg/gpg.conf

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

# A work around for a setpgid error when running crond -f directly as the CMD
RUN echo "#!/bin/sh" > /cron-cmd.sh
RUN echo "set -e" >> /cron-cmd.sh
RUN echo "crond -f" >> /cron-cmd.sh
RUN chmod +x /cron-cmd.sh

# Run cron.....
CMD ["/cron-cmd.sh"]
