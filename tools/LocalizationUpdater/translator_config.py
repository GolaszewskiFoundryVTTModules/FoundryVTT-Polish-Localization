import os
import datetime

# --- LOGGING ---
LOG_DIR = "tools/LocalizationUpdater/Logs"
CURRENT_TIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILENAME = os.path.join(LOG_DIR, f"LocalizationUpdate_{CURRENT_TIME}.log")

# --- CORE TRANSLATION PATHS ---
CORE_EN_DIR = "lang/en/"
CORE_PL_DIR = "lang/pl/"

# --- SOURCE DATA DIRECTORY ---
SOURCE_DATA_DIR = "downloaded-source/"

# --- TEMPORARY & OUTPUT PATHS ---
TEMP_CORE_EN_DIR = "tools/LocalizationUpdater/OldLocale/"

# --- CORE FILE MAPPINGS & LISTS ---
CORE_FILE_PAIRS = [
    ("en", "pl"),
]

# Files that are considered complete and need verbose logging
COMPLETED_FILES = [
    "lang/pl.json",
]