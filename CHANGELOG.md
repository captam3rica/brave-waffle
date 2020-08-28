# Brave Waffle Change Log
All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Year Notation Versioning.


## Types of Changes

- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities.

## [v0.0.10dev] - 2020-08-27

- **Added** - Ability to pull a list of departments currently in the Jamf instance.
- **Added** - Ability to retry after connection timeout when deleting departments and/or buildings.
- **Added** - progress bar to some of the actions that take longer and normal amounts of time to complete.
- **Fixed** - Updated department delete function to utilize the master department list that is pulled at the begginning of the run then use that to compare against the input file. Increase time when looking for departments that are not in the Jamf console because we removed the extra API call.
- **Changed** - A few reporting output updates.

## [v0.0.9dev] - 2020-07-22

- **Added** - Ability to delete buildings from Jamf.
- **Fixed** - Items from input file and items from Jamf will now be compared using their lowercase varient for better consistency.


## [v0.0.8dev] - 2020-06-02

- **Fixed** - Updated to account for other character encodings link `'\u017d'` = Ž. All API payloads are now encoded with `utf-8` encoding before being sent.
- **Fixed** - Switched back to the Classic API to pull all building information from Jamf Pro. There appears to be a limitation of the first 2000 records in the new Jamf Pro swagger API.
- **Changed** - Refactored coded. 

## [v0.0.7dev] - 2020-06-02

- **Added** - Ability to delete Jamf Departments via CSV template file.
- **Added** - Ability to request a new bearer token if the expiration threshold is reached.


## [v0.0.6dev] - 2020-06-01

- **Added** - Ability to add Jamf buildings and Jamf departments via CSV template file.


## ToDo

- **Fix** - When deleting buildings and departments add fix to convert inpout value and what is found in Jamf to lower case before making the comparison.
- **Add** - ability to add smartgroups based on xml template input.
- **Add** - Report capability that pulls all Computers and/or all mobile devices from a Jamf instance.
	- Name, SerialNumber, MAC Address, Building, Department, Username, Last inventory update, last checkin date, macOS version, iOS Version, iPadOS Version, 

