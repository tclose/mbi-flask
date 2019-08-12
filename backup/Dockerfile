FROM alpine:3.9

LABEL maintainer="Tom Close <tom.g.close@gmail.com>"

#install postgres client
RUN apk update \
 && apk add --no-cache --virtual .build-deps \
 dcron

COPY crontab /etc/crontab

# add the backup script
COPY backup.sh /backup.sh
RUN chmod +x /backup.sh

# add the restore script
COPY restore.sh /restore.sh
RUN chmod +x /restore.sh

# Run cron.....
CMD ["crond", "-f"]
