ezbackup
========

[![Code Climate](https://codeclimate.com/github/tux-00/ezbackup/badges/gpa.svg)](https://codeclimate.com/github/tux-00/ezbackup)

Save a list of files/dirs into a tarball archive and move it to local storage or FTP server. Run summary can be sent by mail.

## Dependencies
ezbackup simply works with python2 or python3, **no dependencies**.

## Usage
- ezbackup.conf : configure informations of FTP connection and some various options for ezbackup
- save.list : list of files and/or dirs to be saved (filename can be changed)

Run ezbackup:
```
python ezbackup.py
```
