import os
import time
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

class RecordingsManager:
    recording_retention_period_in_days: int
    recording_size_limit_in_mb: int

    def __init__(self, config):
        self.download_path = config.download_path
        self.recording_retention_period_in_days = config.recording_retention_period_in_days
        self.recording_size_limit_in_mb = config.recording_size_limit_in_mb

    def check_recording_limits(self):
        message = f"Checking for recordings to delete..."
        logger.info(message)

        files = [os.path.join(self.download_path, f) for f in os.listdir(self.download_path)]
        augmented_files = [
            {"filename": f, "size": os.stat(f).st_size, "mod_time": os.stat(f).st_mtime, "deleted": False}
            for f in files
        ]
        augmented_files = sorted(augmented_files, key=lambda f: f["mod_time"], reverse=True)

        if augmented_files:
            augmented_files = self.__check_time_limit(augmented_files)
            augmented_files = self.__check_size_limit(augmented_files)

        return augmented_files

    def __check_time_limit(self, files):
        if self.recording_retention_period_in_days > 0:
            current_day_limit = int(time.time()) - (self.recording_retention_period_in_days * 24 * 60 * 60)
            for f in files:
                if f["mod_time"] < current_day_limit:
                    message = f"Too old recording, deleting {f["filename"]}... "
                    logger.info(message)
                    os.remove(f["filename"])
                    f["deleted"] = True

        return [f for f in files if not f["deleted"]]

    def __check_size_limit(self, files):
        if self.recording_size_limit_in_mb > 0:
            sum_size = 0
            for f in files:
                if sum_size > self.recording_size_limit_in_mb:
                    message = f"Recordings exceeding size limit, deleting {f["filename"]}..."
                    logger.info(message)
                    os.remove(f["filename"])
                    f["deleted"] = True
                sum_size += (f["size"] / 1024 / 1024)

        return [f for f in files if not f["deleted"]]
