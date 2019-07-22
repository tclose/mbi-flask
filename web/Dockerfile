FROM tomcat:7-jre8-alpine

MAINTAINER Tom Close <tom.g.close@gmail.com>

# Make directories required for XNAT
RUN mkdir -p /data/xnat/home/config
RUN mkdir -p /data/xnat/home/work
RUN mkdir -p /data/xnat/archive
RUN mkdir -p /data/xnat/prearchive
RUN mkdir -p /data/xnat/build
RUN mkdir -p /data/xnat/cache
RUN mkdir -p /data/xnat/ftp
RUN mkdir -p /data/xnat/pipeline

EXPOSE 8080
EXPOSE 8009
RUN rm -rf $CATALINA_HOME/webapps
VOLUME "$CATALINA_HOME/webapps"

# Set timezone
ARG TIMEZONE
RUN apk add --no-cache postgresql-client
RUN apk add --no-cache postgresql-client tzdata
RUN echo $TIMEZONE
RUN ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime
RUN echo $TIMEZONE > /etc/timezone
ENV TZ $TIMEZONE
RUN apk del tzdata
# && rm -rf /var/cache/apk/*

# Launch Tomcat
CMD ["/usr/local/tomcat/bin/catalina.sh", "run"]
