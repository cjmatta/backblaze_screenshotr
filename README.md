# Backblaze Screenshoter
A simple python script for macos to take a screenshot and upload to Backblaze B2

Set the following environment variables:
* B2_KEY
* B2_KEY_ID
* B2_BUCKET_NAME

```
usage: b2_screenshot_uploader.py [-h] --directory DIRECTORY [-a | -w | -s]

Screenshot uploader to B2

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY
                        Directory for output
  -a, --area            screenshot of a selected area
  -w, --window          screenshot of the current active window
  -s, --screen          screenshot of the whole screen
  ```
