# Specify base image
FROM python:3.9.7-alpine as base

# Build dependencies in python
FROM base as builder

# Install every build dependencies in builder image
RUN apk add gcc musl-dev --no-cache
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python-dev
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
ENTRYPOINT python ./streamlink-recorder.py -user=${user} -timer=${timer} -quality=${quality} -clientid=${clientid} -clientsecret=${clientsecret} -appriseargs="${appriseargs}" -gamelist="${gamelist}" -streamlinkargs="${streamlinkargs}" -recordingsizelimit="${recordingsizelimit}" -recordingretention="${recordingretention}"
