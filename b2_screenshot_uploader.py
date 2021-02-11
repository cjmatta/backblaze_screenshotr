#!/usr/bin/env python
# strange little app to let me upload screenshots to backblaze
import logging
import os
import sys
import subprocess
import argparse
from datetime import date
from wonderwords import RandomWord
from b2sdk.v1 import InMemoryAccountInfo, B2Api


logging.basicConfig(level="INFO")

def take_area_screenshot(filePath):
    logging.debug("Take area screenshot")
    r = subprocess.run(["screencapture", "-is", filePath], check=True)
    logging.debug("subprocess return code: " + str(r.returncode))

def take_window_screenshot(filePath):
    logging.debug("Take window screenshot")
    r = subprocess.run(["screencapture", "-iW", filePath], check=True)
    logging.debug("subprocess return code: " + str(r.returncode))

def take_screenshot(filePath):
    logging.debug("Take screenshot")
    r = subprocess.run(["screencapture", "-S", filePath], check=True)
    logging.debug("subprocess return code: " + str(r.returncode))

def parse_args():
    parser = argparse.ArgumentParser(description='Screenshot uploader to B2')
    parser.add_argument('--directory', required=True,
                        help="Directory for output")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--area', action='store_true',
                        help='screenshot of a selected area')
    group.add_argument('-w', '--window', action='store_true',
                        help='screenshot of the current active window')
    group.add_argument('-s', '--screen', action='store_true',
                        help='screenshot of the whole screen')
    
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    
    return parser.parse_args()

def run():
    if "B2_KEY_ID" not in os.environ.keys():
        logging.error("Please set environment variables: B2_KEY_ID and B2_KEY")
        sys.exit(1)
    B2_KEY_ID = os.environ['B2_KEY_ID']
    B2_KEY = os.environ['B2_KEY']
    B2_BUCKET_NAME = os.environ['B2_BUCKET_NAME']
    args = parse_args()
    logging.debug("Args: {}".format(args))

    screenshotFolder = os.path.abspath(args.directory)
    logging.debug("Configured screenshotsFolder: {}".format(args.directory))
    
    if not os.path.isdir(screenshotFolder):
        logging.error("File {screenshotFolder} doesn't exist!")
        exit(1)
    
    today = date.today()

    # Initialize B2Api
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_KEY)
    bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)
    # build random word string for filename
    r = RandomWord()
    randwords = '-'.join([
        r.word(include_parts_of_speech=["verbs"]),
        "the",
        r.word(include_parts_of_speech=["adjectives"]),
        r.word(include_parts_of_speech=["nouns"])
    ])
    
    fileName = "{}.png".format(randwords)
    logging.debug("Filename {}".format(fileName))
    fullFile = os.path.join(screenshotFolder, fileName)
    logging.debug("Full file path: {}".format(fullFile))
    
    if args.area:
        take_area_screenshot(fullFile)
    if args.window:
        take_window_screenshot(fullFile)
    if args.screen:
        take_screenshot(fullFile)
    
    uploadResults = bucket.upload_local_file(
        local_file=fullFile,
        file_name=fileName
    )
    fileId = uploadResults.as_dict()['fileId']
    print(b2_api.get_download_url_for_file_name(B2_BUCKET_NAME, fileName))

    


if __name__ == '__main__':
    run()