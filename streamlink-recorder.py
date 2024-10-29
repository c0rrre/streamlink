"""
This script checks if a user on twitch is currently streaming and 
then records the stream via streamlink
"""
import datetime
import argparse
import os
import re
import time
import logging
import sys

from recordings_manager import RecordingsManager
from twitch_manager import TwitchManager, StreamStatus
from streamlink_manager import StreamlinkManager
from notification_manager import NotificationManager

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

class AppConfig:
    def __init__(self, args):
        self.timer = args.timer
        self.user = args.user
        self.quality = args.quality
        self.client_id = args.clientid
        self.client_secret = args.clientsecret
        self.game_list = args.gamelist
        self.slack_id = args.slackid
        self.telegram_bot_token = args.telegrambottoken
        self.telegram_chat_id = args.telegramchatid
        self.oauth_token = args.oauthtoken
        self.recording_size_limit_in_mb = args.recordingsizelimit
        self.recording_retention_period_in_days = args.recordingretention
        self.download_path = args.downloadpath
        self.notify_on_startup = args.notifyonstartup

def loop_check(config, message):
    twitch_manager = TwitchManager(config)
    streamlink_manager = StreamlinkManager(config)
    notifier_manager = NotificationManager(config)
    recordings_manager = RecordingsManager(config)

    if config.notify_on_startup:
        notifier_manager.notify_all(message)

    while True:
        recordings_manager.check_recording_limits()

        stream_status, title = twitch_manager.check_user(config.user)
        if stream_status == StreamStatus.ONLINE:
            safe_title = re.sub(r"[^\w\s._:-]", "", title)
            safe_title = os.path.basename(safe_title)
            filename = f"{config.user} - {datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')} - {safe_title}.mp4"
            recorded_filename = os.path.join("./download/", filename)
            message = f"Recording {config.user} ..."
            notifier_manager.notify_all(message)
            logger.info(message)
            streamlink_manager.run_streamlink(config.user, recorded_filename)
            message = f"Stream {config.user} is done. File saved as {filename}. Going back to checking.."
            logger.info(message)
            notifier_manager.notify_all(message)
        time.sleep(config.timer)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-download_path", default="/download/", help="Path where recordings should be stored")
    parser.add_argument("-timer", type=int, default=240, help="Stream check interval (less than 15s are not recommended)")
    parser.add_argument("-user", required=True, help="Twitch user that we are checking")
    parser.add_argument("-quality", default="720p60,720p,best", help="Recording quality")
    parser.add_argument("-clientid", required=True, help="Your Twitch app client id")
    parser.add_argument("-clientsecret", required=True, help="Your Twitch app client secret")
    parser.add_argument("-slackid", help="Your slack app client id")
    parser.add_argument("-gamelist", default="", help="The game list to be recorded")
    parser.add_argument("-telegrambottoken", help="Your Telegram bot token")
    parser.add_argument("-telegramchatid", help="Your Telegram chat ID where the bot will send messages")
    parser.add_argument("-oauthtoken", help="Your OAuth token for Twitch API")
    parser.add_argument("-recordingsizelimit", default="0", help="Older recordings will be deleted so the remaining will take up space upto the given limit in MBs")
    parser.add_argument("-recordingretention", default="0", help="Recording older than the given limit (in days) will be deleted")
    parser.add_argument("-notifyonstartup",help="Send a notification on startup")
    args = parser.parse_args()

    return AppConfig(args)

def main():
    config = parse_arguments()
    message = f"Checking for {config.user} every {config.timer} seconds. Record with {config.quality} quality."
    logger.info(message)
    loop_check(config, message)

if __name__ == "__main__":
    main()
