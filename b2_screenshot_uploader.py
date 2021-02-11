#!/usr/bin/env python
# strange little app to let me upload screenshots to backblaze
import logging
import os
import sys
import subprocess
import argparse
from datetime import date
import requests
from string import Template
import hashlib
from urllib import parse
import random
import string


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


class B2:
    def __init__(self, B2_KEY_ID, B2_KEY):
        self.B2_KEY_ID = B2_KEY_ID
        self.B2_KEY = B2_KEY
        self.B2_AUTHORIZE_URL = "https://api.backblazeb2.com/b2api/v2/b2_authorize_account"
        self.B2_API_URL = None
        self.B2_UPLOAD_URL = None
        self.B2_DOWNLOAD_URL = None
        self.B2_AUTH_TOKEN = None
        self.B2_UPLOAD_AUTH_TOKEN = None
        self.authorized = False
        self.B2_BUCKET_ID = None

        self.authorize()
        self.getUploadUrl()
    
    def authorize(self):
        r = requests.get(self.B2_AUTHORIZE_URL, auth=(self.B2_KEY_ID, self.B2_KEY))
        if (r.status_code != 200):
            logging.error("B2 Authorization Failed!")
            sys.exit(1)
        self.authorized = True
        authInfo = r.json()
        logging.debug("authinfo: {}".format(r.text))
        self.authorizationToken = authInfo['authorizationToken']
        self.B2_API_URL = authInfo['apiUrl']
        self.B2_DOWNLOAD_URL = authInfo['downloadUrl']
        self.B2_BUCKET_ID = authInfo['allowed']['bucketId']
        self.B2_AUTH_TOKEN = authInfo['authorizationToken']

    def get_file_hash(self, fullFile):
        BUFF_SIZE = 2**10
        sha1 = hashlib.sha1()

        with open(fullFile, 'rb') as f:
            while True:
                data = f.read(BUFF_SIZE)
                if not data:
                    break
                sha1.update(data)
        logging.debug("File sha1: {}".format(sha1.hexdigest()))
        return sha1.hexdigest()

    def getUploadUrl(self):
        url = self.B2_API_URL + "/b2api/v2/b2_get_upload_url"
        payload = {'bucketId': self.B2_BUCKET_ID}
        headers = {'Authorization': self.B2_AUTH_TOKEN}
        logging.debug("data: {}\nheaders: {}".format(payload, headers))
        r = requests.get(url, params=payload, headers=headers)
        getUploadInfo = r.json()
        logging.debug("uploadinfo: {}".format(r.text))
        self.B2_UPLOAD_URL = getUploadInfo['uploadUrl']
        self.B2_UPLOAD_AUTH_TOKEN = getUploadInfo['authorizationToken']

    def uploadFile(self, fullFile):
        fileUploadHeaders = {
            'Authorization': self.B2_UPLOAD_AUTH_TOKEN,
            'X-Bz-File-Name': os.path.basename(fullFile),
            'Content-Type': 'image/png',
            'X-Bz-Content-Sha1': self.get_file_hash(fullFile),
            'X-Bz-Info-Author': parse.quote("Chris Matta")
        }

        logging.debug("File Upload Headers: {}".format(fileUploadHeaders))
        
        r = requests.post(self.B2_UPLOAD_URL, headers=fileUploadHeaders, data=open(fullFile, 'rb'))
        logging.debug(r.text)
        if (r.status_code != 200):
            logging.error("Upload problem!")
            sys.exit(1)
        fileInfo = r.json()
        
        return self.B2_DOWNLOAD_URL + '/b2api/v2/b2_download_file_by_id?fileId=' + fileInfo['fileId']
    


def upload_to_b2(fullFile, B2_KEY_ID, B2_KEY):
    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    # try:
    #     import http.client as http_client
    # except ImportError:
    #     # Python 2
    #     import httplib as http_client
    # http_client.HTTPConnection.debuglevel = 1

    b2 = B2(B2_KEY_ID, B2_KEY)

    return b2.uploadFile(fullFile)


   
def run():
    if "B2_KEY_ID" not in os.environ.keys():
        logging.error("Please set environment variables: B2_KEY_ID and B2_KEY")
        sys.exit(1)
    B2_KEY_ID = os.environ['B2_KEY_ID']
    B2_KEY = os.environ['B2_KEY']
    args = parse_args()
    logging.debug("Args: {}".format(args))

    screenshotFolder = os.path.abspath(args.directory)
    logging.debug("Configured screenshotsFolder: {}".format(args.directory))
    
    if not os.path.isdir(screenshotFolder):
        logging.error("File {screenshotFolder} doesn't exist!")
        exit(1)
    
    today = date.today()

    # get the node of a uuid to use in the file
    randString = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    fileName = "Screenshot-{}_{}.png".format(today.isoformat(), randString)
    logging.debug("Filename {}".format(fileName))
    fullFile = os.path.join(screenshotFolder, fileName)
    logging.debug("Full file path: {}".format(fullFile))
    
    if args.area:
        take_area_screenshot(fullFile)
    if args.window:
        take_window_screenshot(fullFile)
    if args.screen:
        take_screenshot(fullFile)
    
    downloadUrl = upload_to_b2(fullFile, B2_KEY_ID, B2_KEY)
    print(downloadUrl)
    


if __name__ == '__main__':
    run()