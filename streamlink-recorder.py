import argparse
import time
import apprise

from twitch.stream_check import StreamCheck
from twitch.stream_check_service import TwitchStreamCheckService
from recording.stream_recorder_service import StreamRecorderService
from recording.record_retention_service import RecordRetentionService

## enable extra logging
# import logging
# import sys
# log = logging.getLogger('requests_oauthlib')
# log.addHandler(logging.StreamHandler(sys.stdout))
# log.setLevel(logging.DEBUG)

# Constants
SAVE_PATH = "/download/"

# Init variables with some default values
timer = 30
user = ""
quality = "best"
client_id = ""
client_secret = ""
token = ""
game_list = []
apprise_list = []
notify_on_startup = False
streamlink_args = ""
recording_size_limit_in_mb = 0
recording_retention_period_in_days = 3
display_offline_message = 2
apprise_obj = apprise.Apprise()

# Services
stream_check_service: TwitchStreamCheckService = None
stream_recorder_service: StreamRecorderService = None
record_retention_service: RecordRetentionService = None


def loopcheck(do_delete):
    info = stream_check_service.check_user(user)
    status = info["status"]
    stream_data = info["data"]
    global display_offline_message

    if status == StreamCheck.USER_NOT_FOUND:
        print("Streamer with username {} not found. Invalid username?".format(user))
        return
    elif status == StreamCheck.ERROR:
        print("Unexpected error, try again later...")
    elif status == StreamCheck.OFFLINE and display_offline_message:
        print(user, "Stream currently offline, checking again in", timer, "seconds...")
        display_offline_message -= 1
    elif status == StreamCheck.UNWANTED_GAME:
        print("Game in stream is not in the whitelist, checking again in", timer, "seconds...")
    elif status == StreamCheck.ONLINE:
        print("Trying to send notification via apprise...")
        apprise_obj.notify(title="Streamlink", body="Started recording for user '{user}'".format(user=user))
        stream_recorder_service.start_recording(
            stream_data,
            quality=quality,
            do_delete=do_delete,
            streamlink_args=streamlink_args)

        # Wait for problematic stream parts to pass
        time.sleep(10)
        loopcheck(do_delete=False)


def main():
    global timer
    global user
    global quality
    global client_id
    global client_secret
    global apprise_obj
    global apprise_list
    global notify_on_startup
    global game_list
    global streamlink_args
    global recording_size_limit_in_mb
    global recording_retention_period_in_days

    global stream_check_service
    global stream_recorder_service
    global record_retention_service

    parser = argparse.ArgumentParser()
    parser.add_argument("-timer",
                        default="300",
                        help="Stream check interval (less than 15s are not recommended)")
    parser.add_argument("-user",
                        help="Twitch user that we are checking")
    parser.add_argument("-quality",
                        default="best",
                        help="Recording quality")
    parser.add_argument("-gamelist",
                        help="The game list to be recorded")

    parser.add_argument("-clientid",
                        help="Your twitch app client id")
    parser.add_argument("-clientsecret",
                        help="Your twitch app client secret")

    parser.add_argument("-appriseargs",
                        help="Your apprise service arguments, seperated by comma")
    parser.add_argument("-notifyonstartup",
                        help="Send a apprise notification on startup")

    parser.add_argument("-streamlinkargs",
                        default="",
                        help="Additional arguments for streamlink")

    parser.add_argument("-recordingsizelimit",
                        default="0",
                        help="Older recordings will be deleted so the remaining will take up space upto the given limit in MBs")
    parser.add_argument("-recordingretention",
                        default="0",
                        help="Recording older than the given limit (in days) will be deleted")
    args = parser.parse_args()

    if args.timer is not None and args.timer != "":
        timer = int(args.timer)
    if args.user is not None:
        user = args.user
    if args.quality is not None:
        quality = args.quality
    if args.gamelist is not None and args.gamelist != "":
        game_list = args.gamelist.split(",")
    if args.appriseargs is not None and args.appriseargs != "":
        apprise_list = args.appriseargs.split(",")
    if args.notifyonstartup is not None:
        notify_on_startup = args.notifyonstartup
    if args.clientid is not None:
        client_id = args.clientid
    if args.clientsecret is not None:
        client_secret = args.clientsecret
    if client_id is None:
        print("Please create a twitch app and set the client id with -clientid [YOUR ID]")
        return
    if client_secret is None:
        print("Please create a twitch app and set the client secret with -clientsecret [YOUR SECRET]")
        return

    if args.streamlinkargs is not None:
        streamlink_args = args.streamlinkargs
    if args.recordingsizelimit is not None and args.recordingsizelimit != "":
        recording_size_limit_in_mb = int(args.recordingsizelimit)
    if args.recordingretention is not None and args.recordingretention != "":
        recording_retention_period_in_days = int(args.recordingretention)

    for notification_service in apprise_list:
        apprise_obj.add(notification_service)

    record_retention_service = RecordRetentionService(recording_retention_period_in_days, recording_size_limit_in_mb)

    stream_recorder_service = StreamRecorderService(record_retention_service, apprise_obj)
    stream_check_service = TwitchStreamCheckService(client_id, client_secret, game_list)

    print("Checking for", user, "every", timer, "seconds. Record with", quality, "quality.")
    apprise_obj.notify(title="Streamlink",
                       body="Checking for {0} every {1} seconds. Record with {2} quality".format(user, timer, quality))

    # clean up files
    record_retention_service.check_recording_limits()

    while True:
        try:
            loopcheck(do_delete=True)
        except Exception:
            pass
        
        time.sleep(timer)


if __name__ == "__main__":
    # execute only if run as a script
    main()
