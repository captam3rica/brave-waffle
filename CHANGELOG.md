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


## [v0.0.8dev] - 2020-06-02

- **Fixed** - Updated to account for other character encodings link `'\u017d'` = Ž. All API payloads are now encoded with `utf-8` encoding before being sent.
- **Fixed** - Switched back to the Classic API to pull all building information from Jamf Pro. There appears to be a limitation of the first 2000 records in the new Jamf Pro swagger API.
- **Changed** - Refactored coded. 

## [v0.0.7dev] - 2020-06-02

- **Added** - Ability to delete Jamf Departments via CSV template file.
- **Added** - Ability to request a new bearer token if the expiration threshold is reached.


## [v0.0.6dev] - 2020-06-01

- **Added** - Ability to add Jamf buildings and Jamf departments via CSV template file.

