import os
import datetime

log_directory = "tools/LocalizationUpdater/Logs"
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join(log_directory, f"LocalizationUpdate_{current_time}.log")

temp_en_old_directory = "tools/LocalizationUpdater/OldLocale/"
core_en_directory = "lang/en/"
core_pl_directory = "lang/pl/"

en_to_pl_file_pairs = [
    ("en", "pl"),
]
