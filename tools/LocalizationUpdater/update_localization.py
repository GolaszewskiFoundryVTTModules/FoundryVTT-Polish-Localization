import os
import datetime
import logging
import shutil
import argparse
from colorama import Fore, Style, init as colorama_init
from localization_updater import LocalizationUpdater
from translator_config import (
    LOG_DIR, LOG_FILENAME, TEMP_CORE_EN_DIR, CORE_EN_DIR, CORE_PL_DIR, 
    CORE_FILE_PAIRS, COMPLETED_FILES, SOURCE_DATA_DIR
)


class SectionalLogger:
    """A helper class to only print section headers when there is content to log."""
    def __init__(self, console_header, log_file_header):
        self.console_header = console_header
        self.log_file_header = log_file_header
        self._header_printed = False

    def print_header_if_needed(self):
        """Prints the console and file log headers if they haven't been printed yet."""
        if not self._header_printed:
            print(self.console_header)
            logging.info(self.log_file_header)
            self._header_printed = True


def _merge_directories(src, dst):
    """Recursively merges src directory into dst directory, overwriting files."""
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        if os.path.isdir(src_path):
            _merge_directories(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

def _copy_files_and_directories(src_directory, dst_directory):
    """
    Recursively copy all files and directories from the source directory 
    to the destination directory. Existing files in the destination directory 
    with the same name will be overwritten.
    """
    if os.path.exists(dst_directory):
        shutil.rmtree(dst_directory)
    os.makedirs(dst_directory)

    for item in os.listdir(src_directory):
        src_path = os.path.join(src_directory, item)
        dst_path = os.path.join(dst_directory, item)
        if os.path.isdir(src_path):
            if os.path.exists(dst_path):
                _copy_files_and_directories(src_path, dst_path)
            else:
                shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

def _update_source_data():
    """Updates source data from downloaded-source directory."""
    print("\nUpdating source data from downloaded-source directory...")
    
    if not os.path.exists(SOURCE_DATA_DIR):
        print(f"{Fore.YELLOW}Warning: {SOURCE_DATA_DIR} directory not found.{Style.RESET_ALL}")
        print(f"Run 'npm run download' first to download source files from server.")
        return False
    
    source_en = os.path.join(SOURCE_DATA_DIR, "en.json")
    if not os.path.exists(source_en):
        print(f"{Fore.RED}Error: Source file {source_en} not found.{Style.RESET_ALL}")
        return False
    
    # Copy downloaded source to lang/en/
    dest_en = os.path.join(CORE_EN_DIR, "en.json")
    os.makedirs(os.path.dirname(dest_en), exist_ok=True)
    shutil.copy2(source_en, dest_en)
    print(f"Updated {dest_en} from downloaded source")
    
    return True

def _process_core_translations(file_pairs, perform_regex_translate, verbose_flag):
    core_logger = SectionalLogger("\nProcessing core system translations...", "\n=== Core Translations ===")
    
    for en_name, pl_name in file_pairs:
        en_old_path = os.path.join(TEMP_CORE_EN_DIR, en_name + ".json")
        en_path = os.path.join(CORE_EN_DIR, en_name + ".json")
        pl_path = os.path.join(CORE_PL_DIR, pl_name + ".json")

        # Check if the English source file exists
        if not os.path.exists(en_path):
            print(f"{Fore.RED}Error: English source file not found: {en_path}")
            print(f"       Run 'npm run download' to fetch source files.{Style.RESET_ALL}")
            continue

        # Check if the Polish file exists
        if not os.path.exists(pl_path):
            if verbose_flag:
                print(f"Polish file at {pl_path} does not exist. Creating a copy from {en_path}.")
            os.makedirs(os.path.dirname(pl_path), exist_ok=True)
            shutil.copy(en_path, pl_path)
            if verbose_flag:
                print(f"Polish file copied from {en_path} to {pl_path}.")

        # Check if the file is marked as completed
        is_completed = pl_path in COMPLETED_FILES 
        effective_verbose = verbose_flag or is_completed
        
        # Check if backup exists for comparison
        if not os.path.exists(en_old_path):
            print(f"{Fore.CYAN}Info: New file detected (no previous backup): {en_name}. All content will be treated as new.{Style.RESET_ALL}")
            os.makedirs(os.path.dirname(en_old_path), exist_ok=True)
            with open(en_old_path, 'w', encoding='utf-8') as f:
                f.write("{}")
        
        log_identifier = f"core/{os.path.basename(pl_path)}"
        updater = LocalizationUpdater(en_old_path, en_path, pl_path, effective_verbose, log_identifier, logger=core_logger)
        updater.process(perform_regex_translate)


def main():
    colorama_init(autoreset=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(level=logging.INFO, filename=LOG_FILENAME, filemode='w', format='%(message)s')

    parser = argparse.ArgumentParser(description='Run the localization update script.')
    parser.add_argument('--UpdateSourceData', action='store_true', help='Update source data from downloaded-source directory.')
    parser.add_argument('--PerformRegexTranslate', action='store_true', help='Forces re-processing all strings by regex translations.')
    parser.add_argument('-v', '--Verbose', action='store_true', help='Enable verbose logging.')
    args = parser.parse_args()

    update_source_data = args.UpdateSourceData
    perform_regex_translate = args.PerformRegexTranslate
    verbose = args.Verbose

    # Backup the old localization source for comparison before any processing
    print("\nBacking up current core English translations for comparison...")
    _copy_files_and_directories(CORE_EN_DIR, TEMP_CORE_EN_DIR)

    # Update the source files if requested
    if update_source_data:
        if not _update_source_data():
            print(f"{Fore.YELLOW}Continuing with existing source files...{Style.RESET_ALL}")

    # Process core translations
    _process_core_translations(CORE_FILE_PAIRS, perform_regex_translate, verbose)
        
    # Remove old localization source after processing
    if os.path.exists(TEMP_CORE_EN_DIR):
        print("\nRemoving temporary backup of old core English translations...")
        shutil.rmtree(TEMP_CORE_EN_DIR)
    
    print(f"\n{Fore.GREEN}✓ Localization update completed!{Style.RESET_ALL}")
    print(f"Check the log file at: {LOG_FILENAME}")


if __name__ == "__main__":
    main()
