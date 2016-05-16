#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ftplib as ftp
import sys
import tarfile
import smtplib
from datetime import datetime, timedelta
from time import time

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Copy file or dir


def cp(path):
    global nb_files
    global disk_size

    if os.path.isdir(path):
        for object in os.listdir(path):
            cp(os.path.join(path, object))
    else:
        try:
            tar.add(path)
        except Exception as e:
            _print("Error adding {0} file to tar archive: {1}.".format(
                path, e.strerror))
            quit_ezbackup(ERROR_CODE)
        nb_files = nb_files + 1
        disk_size = disk_size + os.path.getsize(path)

    return True

# Connect to the ftp server


def ftp_connect(host, port, login, passwd, dir):
    try:
        ftp.connect(host, port)
    except Exception as e:
        _print("Connection to {0} failed: {1}.".format(host, e.strerror))
        quit_ezbackup(ERROR_CODE)
    try:
        ftp.login(login, passwd)
    except Exception as e:
        _print("Login error: {0}.".format(e.message))
        quit_ezbackup(ERROR_CODE)
    try:
        ftp.cwd(FTP_SAVE_DIR)
    except Exception as e:
        _print("Error changing FTP directory to {0}: {1}.".format(
            FTP_SAVE_DIR, e.message))
        ftp_quit()
        quit_ezbackup(ERROR_CODE)

    _print("Logged as " + login + " on " + host + ":" + str(port))
    _print("Changed dir to " + FTP_SAVE_DIR)
    _print("\nTYPE\tPATH")

    return True

# Convert bytes in Ki, Mi, Gi ...


def sizeof(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

# Send an email


def mail(sender, receivers, subject, msg):
    try:
        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(sender, receivers, 'Subject: %s\n\n%s' % (subject, msg))
    except Exception as e:
        _print("Error sending email to {0} : {1}.".format(
            receivers, e.strerror))
        return False

    _print("Email sent to {0}.".format(", ".join(receivers)))

    return True

# Convert seconds in hour, minutes ...


def get_time(_seconds):
    sec = timedelta(seconds=_seconds)
    exec_time = datetime(1, 1, 1) + sec

    if _seconds < 60:
        return "{0:.3f}s".format(_seconds)
    elif _seconds >= 60 and _seconds < 3600:
        return "{0}m {1}s".format(exec_time.minute, exec_time.second)
    elif _seconds >= 3600:
        return "{0}h {1}m {2}s".format(exec_time.hour, exec_time.minute, exec_time.second)
    else:
        return False

# Exit and send an email if necessary


def quit_ezbackup(exit_code=0):
    global LOCAL_SAVE_DIR

    # Remove archive if exist
    if "tarname" in globals() and os.path.isfile(tarname) and LOCAL_SAVE_ENABLED is False:
        os.remove(tarname)
    elif LOCAL_SAVE_ENABLED and LOCAL_SAVE_DIR != "." and LOCAL_SAVE_DIR != "./" and os.path.exists(LOCAL_SAVE_DIR):
        if LOCAL_SAVE_DIR[-1:] != "/":
            LOCAL_SAVE_DIR = LOCAL_SAVE_DIR + "/"
        try:
            os.rename(tarname, os.path.normpath(LOCAL_SAVE_DIR + tarname))
        except:
            _print("Error moving {0}: {1}.".format(tarname, e.strerror))

    # Quit FTP connection
    if "ftp" in globals() and "HOST" in globals():
        try:
            ftp.quit()
            _print("\nConnection to {0} closed.".format(HOST))
        except:
            pass

    # Send email if configured
    if "MAIL_STATE" in globals() and "MAIL_FAILS" in globals() and "MAIL_ALWAYS" in globals():
        if exit_code == ERROR_CODE and (MAIL_STATE == MAIL_FAILS or MAIL_STATE == MAIL_ALWAYS):
            mail(MAIL_SENDER, MAIL_RECEIVERS, "EZBackup Fail", outbuffer)
        elif exit_code == SUCCESS_CODE and MAIL_STATE == MAIL_ALWAYS:
            mail(MAIL_SENDER, MAIL_RECEIVERS, "EZBackup Stats", outbuffer)
    else:
        _print("Error trying to send mail. No configuration loaded.")

    exit(exit_code)

# Print text to stdout and save value in result


def _print(text):
    global outbuffer

    # Print text to stdout
    print (text)

    # Save text in result
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    print (text)
    sys.stdout = old_stdout
    outbuffer = outbuffer + result.getvalue()


if sys.argv[0] != "ezbackup.py":
    os.chdir(os.path.dirname(sys.argv[0]))

# Constants
MAIL_ALWAYS = 2
MAIL_FAILS = 1
MAIL_NEVER = 0
ERROR_CODE = 1
SUCCESS_CODE = 0

# Init the text buffer
outbuffer = ""

# Start timer for the execution time
start_time = time()

# Open and parse the config file for ezbackup
CONF_FILE = 'ezbackup.conf'
config = ConfigParser.RawConfigParser()
config.read(CONF_FILE)

# Load constants from the ezbackup configuration file
try:
    FTP_ENABLED = config.getboolean('FTP', 'ftp_enabled')
    HOST = config.get('FTP', 'host')
    PORT = config.getint('FTP', 'port')
    LOGIN = config.get('FTP', 'login')
    PASSWD = config.get('FTP', 'passwd')
    FTP_SAVE_DIR = config.get('FTP', 'save_dir')
    LOCAL_SAVE_ENABLED = config.getboolean('Options', 'local_save_enabled')
    LOCAL_SAVE_DIR = config.get('Options', 'local_save_dir')
    COMPRESS = config.get('Options', 'compress')
    BACKUP_NAME = config.get('Options', 'backup_name')
    SAVE_LIST = config.get('Options', 'save_list')
    MAIL_STATE = config.getint('Options', 'mail')
    MAIL_SENDER = config.get('Options', 'mail_sender')
    MAIL_RECEIVERS = config.get('Options', 'mail_receivers')
    MAIL_RECEIVERS = MAIL_RECEIVERS.replace(' ', '')
    MAIL_RECEIVERS = MAIL_RECEIVERS.split(',')
except Exception as e:
    _print("Error parsing {0}: {1}.".format(CONF_FILE, e.message))
    quit_ezbackup(ERROR_CODE)

# Maximum recursion (for cp() function)
sys.setrecursionlimit(10000)

# Create the archive
t = datetime.now()
tarname = t.strftime(BACKUP_NAME) + '.tar.' + COMPRESS
try:
    tar = tarfile.open(tarname, 'w:' + COMPRESS)
except Exception as e:
    _print("Error creating {0}: {1}.".format(tarname, e.message))
    quit_ezbackup(ERROR_CODE)

# Open the save list file
try:
    savelist = open(SAVE_LIST, 'r')
except IOError as e:
    _print("Error opening {0}: {1}.".format(SAVE_LIST, e.strerror))
    quit_ezbackup(ERROR_CODE)

if FTP_ENABLED:
    ftp = ftp.FTP()
nb_files = 0
disk_size = 0
tar_size = 0
something_saved = False

# Read each lines of the save list and copy dirs or files
for path in savelist.readlines():
    # If line different from a comment or an empty line
    if path != "\n" and path[0] != ';' and path[0] != '#':
        if something_saved is False:
            if FTP_ENABLED:
                ftp_connect(HOST, PORT, LOGIN, PASSWD, FTP_SAVE_DIR)
            something_saved = True
        path = path.replace('\n', '')
        if os.path.isdir(path):
            _print("[DIR]\t" + path)
        elif os.path.isfile(path):
            _print("[FILE]\t" + path)
        cp(path)

savelist.close()
tar.close()

# If there is something to save
if something_saved:
    with open(tarname, 'rb') as savedtar:
        if FTP_ENABLED:
            try:
                ftp.storbinary('STOR ' + tarname, savedtar)
            except Exception as e:
                _print("Error copying {0} to FTP server: {1}.".format(
                    tarname, e.message))
                quit_ezbackup(ERROR_CODE)

        exec_time = time() - start_time
        tar_size = os.path.getsize(tarname)

        _print("\nArchive name : {0}".format(tarname))
        _print("Files copied : {0}".format(nb_files))
        _print("Disk size    : {0}".format(sizeof(disk_size)))
        _print("Archive size : {0}".format(sizeof(tar_size)))
        _print("Exec time    : {0}".format(get_time(exec_time)))
else:
    _print("Nothing to save.")

quit_ezbackup(SUCCESS_CODE)
