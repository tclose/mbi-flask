FROM alpine:3.7

MAINTAINER Manish Kumar <rishimanish123@gmail.com>

#install postgres client
RUN apk update \
 && apk add --no-cache --virtual .build-deps \
 dcron postgresql-client

# disable default crontab

COPY crontab /etc/crontab

# add the backup scripts into root/home
ADD backup.sh /root/backup.sh
RUN chmod +x /root/backup.sh
ADD backup_init.sh /root/backup_init.sh
RUN chmod +x /root/backup_init.sh
RUN mkdir -p /etc/cron.d/

CMD ["/root/backup_init.sh"]
