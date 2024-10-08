# Specify base image
FROM python:3.13.0-alpine as base

# Build dependencies in python
FROM base as builder

# skip rust installation on building cryptography module
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

# fix output of docker container
ENV PYTHONUNBUFFERED=1

# Install every build dependencies in builder image
RUN apk add libffi-dev openssl-dev build-base gcc musl-dev --no-cache
RUN mkdir /install
WORKDIR /install
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --prefix=/install --upgrade streamlink 
RUN pip install --prefix=/install --upgrade oauth2client
RUN pip install --prefix=/install --upgrade oauthlib
RUN pip install --prefix=/install --upgrade requests_oauthlib
RUN pip install --prefix=/install --upgrade pycountry
RUN pip install --prefix=/install --upgrade cryptography
RUN pip install --prefix=/install --upgrade apprise 

# Run in minimal alpine container with no other dependencies
FROM base as runner
COPY --from=builder /install /usr/local
ADD streamlink-recorder.py /
ADD recording/ recording/
ADD twitch/ twitch/

RUN apk add ffmpeg --no-cache

# Configure entrypoint with environment variables (only user is mandatory)
ENTRYPOINT python ./streamlink-recorder.py -user=${user} -timer=${timer} -quality=${quality} -clientid=${clientid} -clientsecret=${clientsecret} -appriseargs="${appriseargs}" -notifyonstartup="${notifyonstartup}" -gamelist="${gamelist}" -streamlinkargs="${streamlinkargs}" -recordingsizelimit="${recordingsizelimit}" -recordingretention="${recordingretention}"
