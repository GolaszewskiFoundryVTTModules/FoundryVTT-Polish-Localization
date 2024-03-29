import os
import json
import logging

import re
from collections import Counter
from tqdm import tqdm
import datetime
import shutil
import subprocess
import argparse

import difflib

class LocalizationUpdater:
    
    def __init__(self, en_old_path, en_path, pl_path):
        # filepaths
        self.en_old_path = en_old_path
        self.en_path = en_path
        self.pl_path = pl_path

        # data containers
        self.en_old_extracted = {}
        self.en_extracted = {}
        self.pl_extracted = {}

        # key operation logs
        self.new_keys = []
        self.removed_keys = []
        self.renamed_keys = []
        self.outdated_keys = []
        self.updated_eng_keys = []


    def get_file_from_directory(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"An error occurred while loading the JSON file: {filepath}: {str(e)}")
            return None

    def save_file_to_directory(self, filepath, data):
        try:
            # Ensure the directory of the file exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the data to the specified filepath
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"An error occurred while saving the JSON file to {filepath}: {str(e)}")

    def extract_localization_dict(self, obj, current_path='', result_dict=None):
        if obj is None:
            return None
        
        if result_dict is None:
            result_dict = {}
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if current_path:
                    # if current path ends with
                    if current_path[-1] == "." and key[0]==" " or key[0]==".":
                        new_path = f'{current_path}{key}'
                    else:
                        new_path = f'{current_path}.{key}'
                else:
                    new_path = key

                self.extract_localization_dict(value, new_path, result_dict)

        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                new_path = f"{current_path}{{{index}}}"
                self.extract_localization_dict(item, new_path, result_dict)
        else:
            result_dict[current_path] = obj

        return result_dict

    def rebuild_nested_json(self, flat_dict):
        nested_json = {}

        for compound_key, value in flat_dict.items():
            # Split the key intelligently based on '.' not followed by whitespace
            keys = [k for k in re.split(r'\.(?![\s.])', compound_key) if k]
            current_level = nested_json

            for i, key in enumerate(keys):
                if '{' in key and '}' in key:
                    # Split the key on the brackets to get the list name and index
                    list_name, list_index = key.replace('}', '').split('{')
                    list_index = int(list_index)
                    
                    # Ensure the list exists and has enough space for the index
                    if list_name not in current_level:
                        current_level[list_name] = []
                    while len(current_level[list_name]) <= list_index:
                        current_level[list_name].append(None)
                    
                    # If it's the last key, set the value
                    if i == len(keys) - 1:
                        current_level[list_name][list_index] = value
                    else:
                        # Prepare for the next level of nesting
                        if current_level[list_name][list_index] is None:
                            current_level[list_name][list_index] = {}
                        current_level = current_level[list_name][list_index]
                else:
                    if i == len(keys) - 1:
                        current_level[key] = value
                    else:
                        if key not in current_level:
                            current_level[key] = {}
                        current_level = current_level[key]

        return nested_json

    def generate_concise_diff(self, old_value, new_value):
        from difflib import SequenceMatcher

        # Create a sequence matcher
        s = SequenceMatcher(None, old_value, new_value)
        diff = []

        for tag, i1, i2, j1, j2 in s.get_opcodes():
            if tag == 'replace':
                diff.append('\n')
                diff.append('      - ' + old_value[i1:i2])
                diff.append('      + ' + new_value[j1:j2])
            elif tag == 'delete':
                diff.append('\n')
                diff.append('      - ' + old_value[i1:i2])
            elif tag == 'insert':
                diff.append('\n')
                diff.append('      + ' + new_value[j1:j2])

        return ''.join(diff)

    def update_localization(self):
        # Count occurrences of each value in both dictionaries
        old_value_counts = Counter(self.en_old_extracted.values())
        new_value_counts = Counter(self.en_extracted.values())

        # Identify unique values in both dictionaries
        unique_old_values = {value for value, count in old_value_counts.items() if count == 1}
        unique_new_values = {value for value, count in new_value_counts.items() if count == 1}

        # Reverse mapping for unique values only
        old_value_to_key = {value: key for key, value in self.en_old_extracted.items() if value in unique_old_values}
        new_value_to_key = {value: key for key, value in self.en_extracted.items() if value in unique_new_values}

        for new_key, new_value in tqdm(self.en_extracted.items(), desc=f"Processing new keys in {os.path.basename(self.pl_path)}"):
            
            # Key is already up to date
            if new_key in self.pl_extracted and self.pl_extracted.get(new_key) == new_value:
                continue

            # rename key if both before and after the value is unique
            old_key = old_value_to_key.get(new_value, None)
            if old_key and old_key != new_key and new_value in unique_new_values:
                # double-check for translated entry existence
                if old_key not in self.pl_extracted:
                    print(f"Did not find old key {old_key} in polish {os.path.basename(self.pl_path)}. It may have been updated already")
                else:
                    self.pl_extracted[new_key] = self.pl_extracted.pop(old_key, None)
                    self.renamed_keys.append((old_key, new_key))
            # if the key exists in translation, and the value changed
            elif new_value != self.en_old_extracted.get(new_key, None) and new_key in self.pl_extracted:
                # if value was kept in english, update it outright
                if self.pl_extracted.get(new_key) == self.en_old_extracted.get(new_key):
                    self.pl_extracted[new_key] = new_value
                    self.updated_eng_keys.append(new_key)
                # else mark it as outdated that needs manual correction
                else:
                    old_value = self.en_old_extracted.get(new_key, "")
                    diff_string = self.generate_concise_diff(old_value, new_value)
                    self.outdated_keys.append((new_key, diff_string))

            # if value does not exist in translation, add it
            elif new_key not in self.pl_extracted:
                self.pl_extracted[new_key] = new_value
                self.new_keys.append(new_key)

        # remove obsolete keys
        for old_key in tqdm(list(self.en_old_extracted.keys()), desc=f"Deleting obsolete keys in {os.path.basename(self.pl_path)}", leave=False):
            if old_key not in self.en_extracted:
                self.pl_extracted.pop(old_key, None)
                self.removed_keys.append(old_key)

    def validate_keys_match(self, path=''):
        errors = []

        for key in self.en_extracted.keys():
            current_path = f"{path}.{key}" if path else key
            if key not in self.pl_extracted:
                errors.append(f"Missing key in target: {current_path}")
            else:
                if isinstance(self.en_extracted[key], dict) and isinstance(self.pl_extracted[key], dict):
                    errors.extend(self.validate_keys_match(self.en_extracted[key], self.pl_extracted[key], current_path))
                elif isinstance(self.en_extracted[key], dict) and not isinstance(self.pl_extracted[key], dict):
                    errors.append(f"Mismatched types at {current_path}, expected a dict in target but found a non-dict.")
                elif not isinstance(self.en_extracted[key], dict) and isinstance(self.pl_extracted[key], dict):
                    errors.append(f"Mismatched types at {current_path}, expected a non-dict in target but found a dict.")

        for key in self.pl_extracted.keys():
            current_path = f"{path}.{key}" if path else key
            if key not in self.en_extracted:
                errors.append(f"Obsolete key in target: {current_path}")

        return errors

    def process(self):

        self.en_old_extracted = self.extract_localization_dict(self.get_file_from_directory(self.en_old_path))
        self.en_extracted = self.extract_localization_dict(self.get_file_from_directory(self.en_path))
        self.pl_extracted = self.extract_localization_dict(self.get_file_from_directory(self.pl_path))

        if self.en_old_extracted is None or self.en_extracted is None or self.pl_extracted is None:
            logging.info(f"{os.path.basename(self.pl_path)}:")
            logging.error("Unable to proceed due to missing data.")
            return

        #Not translated and already up to date. Skipping!
        if self.pl_extracted == self.en_extracted:
            return

        self.update_localization()
        
        # if no keys were modified, return
        if not any([self.new_keys, self.removed_keys, self.renamed_keys, self.updated_eng_keys, self.outdated_keys]):
            return

        # Log the processed file name
        logging.info(f"{os.path.basename(self.pl_path)}:")
        
        if self.new_keys:
            logging.info(f"  Added keys: {len(self.new_keys)}")
            for key in self.new_keys:
                logging.info(f"    {key}")

        if self.removed_keys:
            logging.info(f"  Deleted keys: {len(self.removed_keys)}")
            for key in self.removed_keys:
                logging.info(f"    {key}")

        if self.renamed_keys:
            logging.info(f"  Renamed keys (transferred): {len(self.renamed_keys)}")
            for old_key, new_key in self.renamed_keys:
                logging.info(f"    {old_key} -> {new_key}")

        if self.updated_eng_keys:
            logging.info(f"  Updated english keys: {len(self.updated_eng_keys)}")
            for key in self.updated_eng_keys:
                logging.info(f"    {key}")

        if self.outdated_keys:
            logging.info(f"  Outdated records: {len(self.outdated_keys)}")
            for key, diff in self.outdated_keys:  # Unpack key and diff_string
                logging.info(f"    Key: {key}\n    Diff:{diff}")


        validation_errors = self.validate_keys_match()
        if validation_errors:
            for error in validation_errors:
                logging.error(error)
            logging.error("Validation failed, the keys in English and Polish files do not match.")
        else:
            logging.info("Validation successful, all keys match.")
        
        # sort the dictionary
        ordered_pl = {}

        # Iterate over keys in the template dictionary
        for key in self.en_extracted.keys():
            ordered_pl[key] = self.pl_extracted[key]
        
        self.pl_extracted = ordered_pl

        logging.info("\n")

        self.save_file_to_directory(self.pl_path, self.rebuild_nested_json(self.pl_extracted))
        # re-save en file to ensure same lines 
        self.save_file_to_directory(self.en_path, self.rebuild_nested_json(self.en_extracted))

def copy_files_and_directories(src_directory, dst_directory):
    """
    Recursively copy all files and directories from the source directory 
    to the destination directory. Existing files in the destination directory 
    with the same name will be overwritten.
    """
    if not os.path.exists(dst_directory):
        os.makedirs(dst_directory)
    for item in os.listdir(src_directory):
        src_path = os.path.join(src_directory, item)
        dst_path = os.path.join(dst_directory, item)
        if os.path.isdir(src_path):
            # Recursively copy the entire subdirectory
            if os.path.exists(dst_path):
                # If the subdirectory exists at the destination, recursively copy its contents
                copy_files_and_directories(src_path, dst_path)
            else:
                # If the subdirectory does not exist at the destination, copy it
                shutil.copytree(src_path, dst_path)
        else:
            # Copy files and overwrite if necessary
            shutil.copy2(src_path, dst_path)

def run_js_script(script_path):
    try:
        # Run the .js script with Node.js
        result = subprocess.run(['node', script_path], check=True, text=True, capture_output=True)
        # Output the result (stdout and stderr)
        print(result.stdout)
        print(result.stderr)
    except subprocess.CalledProcessError as e:
        # Handle errors in the called .js script
        print(f"An error occurred while running {script_path}: {e}")

def main():
    # Setup logging configuration
    log_directory = "tools/HelperScripts/Logs"
    os.makedirs(log_directory, exist_ok=True)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_directory, f"LocalizationUpdate_{current_time}.log")
    logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='w', format='%(message)s')

    # Define sets of file paths
    file_sets = []
    
    temp_en_old_directory = "tools/HelperScripts/OldLocale/"
    core_en_directory = "lang/en/"
    core_pl_directory = "lang/pl/"
    
    en_to_pl_file_pairs =  [
        ("en", "pl")
    ]

    for en_name, pl_name in en_to_pl_file_pairs:
        file_sets.append(
            (
                temp_en_old_directory + en_name + ".json",
                core_en_directory + en_name + ".json",
                core_pl_directory + pl_name + ".json"
            )
        )

    for en_old, en, pl in file_sets:
        updater = LocalizationUpdater(en_old, en, pl)
        updater.process()

if __name__ == "__main__":
    main()