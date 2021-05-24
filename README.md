![Code Style: Black](https://img.shields.io/badge/code%20style-black-black) [![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=captam3rica_brave-waffle)

# Brave Waffle
CLI Tool to manipulate information in the Jamf Pro console.

**NOTE**: THE CONTENTS OF THIS REPO ARE A WORK IN PROGRESS ...


### Usage

```
usage: jamfdatamanager.py [-h] --url URL [--update-device-records] [--add-buildings] [--add-departments]
                                [--delete-departments] --filepath FILEPATH [--version] [-v LEVEL]

A tool to update device inventory records and other information in Jamf Pro.

optional arguments:
  -h, --help            show this help message and exit
  --url URL             Jamf Pro tenant url (example.jamfcloud.com).
  --update-device-records
                        Update a list of device records
  --add-buildings       Add one or more buildings to Jamf Pro console.
  --add-departments     Add one or more departments to Jamf Pro console.
  --delete-departments  Remove one or more departments to Jamf Pro console.
  --filepath FILEPATH   Enter path to the spreadsheet(csv file) or drag the file into this Terminal window.
  --version             Show this tools version.
  -v LEVEL, --verbose LEVEL
```
