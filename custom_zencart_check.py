#!/usr/local/bin/python2.7

import csv
import requests
import sys
from optparse import OptionParser
import logging
import logging.handlers

# This version of Python does not have a "true SSLContext" object available. Which we don't need.
# Still, it spews errors all over the place as a consequence. Let's disable these annoying warnings.
requests.packages.urllib3.disable_warnings()

# Global logger
script_logger = logging.getLogger()

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
   parser.add_option("-r","--release",
                      action="store",
                      dest="release",
                      help="Release version of ZenCart to be checked")
   # parser.add_option("-l", "--logserver",
   #                    action="store",
   #                    dest="logserver",
   #                    default="10.0.6.250",
   #                    help="IP address of log server to receive results; defaults to '10.0.6.250'")
   (options, args) = parser.parse_args()

   # handler = logging.handlers.SysLogHandler(address = (options.logserver,514), facility='local5')
   # script_logger.addHandler(handler)

   #
   # # Also want these stored locally.
   # localhandler = logging.handlers.SysLogHandler('/dev/log', facility='local5')
   # script_logger.addHandler(localhandler)

   if not options.release in ['1.3.9f', '1.3.9h', '1.3.8', '1.5.0']:
      error("Warp Core breach in Exercise Control. Asked to check Zen Cart {0}; this is not a supported release. Inform Dr. O'Leary.".format(options.release), options.url, options.release)

   if( (options.passfile is None) or (options.user is None)):
      error("Warp core breach in Exercise Control. Missing the admin user or the password file", options.url, options.release)

   password = "password1!"#get_password(options.passfile, options.user, options.url)

   #############################
   # # Check #1: Get the Zen Cart home page
   # try:
   #    r = requests.get(options.url, verify=False)
   # except Exception as e:
   #    error("Unable to complete the request to {0}.".format(options.url), options.url, options.release)
   #
   # if r.status_code != 200:
   #    error("Unable to complete the request to {0}; server returned status code {1}".format(options.url, r.status_code), options.url, options.release)
   #
   # if options.release in ['1.3.8', '1.3.9f', '1.3.9h']:
   #    required_text = "Congratulations! You have successfully installed your Zen Cart&trade; E-Commerce Solution."
   # else:  # 1.5.0
   #    required_text = "Congratulations! You have successfully installed your Zen Cart&reg; E-Commerce Solution."
   # if not required_text in r.content:
   #       error("Zen Cart {0} page responds, but does not appear to contain the sample shop.".format(options.url), options.url, options.release)
   #
   # required_text = "Powered by <a href=\"http://www.zen-cart.com\" target=\"_blank\">Zen Cart</a></div>"
   # if not required_text in r.content:
   #       error("Zen Cart {0} page responds, but does not appear to contain the sample shop.".format(options.url), options.url, options.release)
   #
   # #############################
   # # Check #2: Price Check for standard product
   # currenturl = options.url + "/index.php?main_page=product_info&cPath=1_4&products_id=1"
   # try:
   #    r = requests.get(currenturl, verify=False)
   # except Exception as e:
   #    error("Unable to complete the request to {0} for the Matrox G200 MMS.".format(currenturl), options.url, options.release)
   # if r.status_code != 200:
   #    error("Unable to complete the request to {0} for the Matrox G200 MMS; server returned status code {1}.".format(currenturl, r.status_code), options.url, options.release)
   #
   # required_text = "Matrox G200 MMS"
   # if not required_text in r.content:
   #       error("Zen Cart {0} page does not appear to be for the Matrox G200 MMS as it ought.".format(currenturl), options.url, options.release)
   #
   # required_text = "Starting at: $"
   # if not required_text in r.content:
   #       error("Zen Cart {0} page for the Matrox G200 MMS responds, but does not appear to contain the price information.".format(currenturl), options.url, options.release)
   #
   # price = r.content.split(required_text)[1].split("</h2>")[0]
   # if not price == "299.99":
   #    error("Zen Cart {0} page for the Matrox G200 MMS responds, but does has the wrong price information. Instead of costing $299.99, it costs ${1}.".format(currenturl,price), options.url, options.release)

   #############################
   # Check #3: Log in to the admin page
   s = requests.Session()

   try:
      r = s.get(options.adminurl, verify=False)
   except Exception as e:
      error("Unable to complete the request to the admin page at {0}.".format(options.adminurl), options.url, options.release)

   if r.status_code != 200:
      error("Unable to complete the request to the admin login page at {0}; server returned status code {1}".format(options.adminurl, r.status_code), options.url, options.release)

   required_text = "Zen Cart!"
   if not required_text in r.content:
         error("Zen Cart admin login page {0} does not appear to have the proper content.".format(options.adminurl), options.url, options.release)

   required_text = "name=\"securityToken\" value=\""
   if not required_text in r.content:
      error("Zen Cart admin page {0} does not appear to have the proper content.".format(options.adminurl), options.url, options.release)
   token = r.content.split(required_text)[1].split("\">")[0]

   if options.release == '1.5.0':
      required_text = "name=\"action\" value=\""
      if not required_text in r.content:
         error("Zen Cart admin page {0} does not appear to have the proper content.".format(options.adminurl), options.url, options.release)
      actiontoken = r.content.split(required_text)[1].split("\"")[0]
   else:  # Older versions don't use this token. Rather than splitting the code below, let's just include an unecessary parameter. It won't hurt. Honest.
      actiontoken="1"

   currenturl = options.adminurl + "/login.php"
   try:   
      r = s.post(currenturl, verify=False,
            data = {'admin_name':options.user,
                    'admin_pass':password,
                    'securityToken':token,
                    'submit':'Login',
                    'action':actiontoken}
                     )
   except Exception as e:
      print (e)
      error("Unable to complete the request to {0}.".format(currenturl), options.url, options.release)

   if r.status_code != 200:
      error("Unable to complete the request to {0}; server returned status code {1}".format(currenturl, r.status_code), loginurl, options.release)

   # If you get sent back to the login page again, well, you didn't login, did you?
   logincontent = "Admin Login"
   if logincontent in r.content:
      error("Unable to authenticate to the Zen Cart admin page {0} as user {1} with provided credentials.".format(currenturl, options.user), options.url, options.release)

   required_text = "My Store</a></li>"
   if not required_text in r.content:
         error("Zen Cart admin page {0} does not appear to have the proper content.".format(currenturl), options.url, options.release)

   required_text = "alt=\"Zen Cart:: the art of e-commerce\""
   if not required_text in r.content:
         error("Zen Cart admin page {0} does not appear to have the proper content.".format(currenturl), options.url, options.release)

   success("All Zen Cart checks passed.", options.url, options.release)

def get_password(passfile, user, server):
   found_password = False
   try:
      passfilecsv = open(passfile, 'rb')
   except:
         error("Warp core breach in Exercise Control. Unable to open the password file {0}. This should not happen. Please let Dr. O'Leary know ASAP!".format(passfile), server, "Indeterminate")

   passfilereader = csv.reader(passfilecsv)
   for row in passfilereader:
      if row[0].strip() == user.strip():
         found_password = True
         password = row[1].strip()
         break
   if(not found_password):
      error("Warp core breach in Exercise Control. The password file on Exercise Control does not have a password for the user {0}. This should not happen. Please let Dr. O'Leary know ASAP!".format(user), server, "Indeterminate")
   return password

def success(reason, url, release):
    host = url.split("/")[2]   
    print (reason)
    print("Exercise Control Zen Cart Check SUCCESS on {0} Checked URL:{1}. Zen Cart Version:{3}. {2}".format(host,url,reason,release))
    sys.exit(0)

def error(reason, url, release):
   host = url.split("/")[2] 
   print (reason)
   print("Exercise Control Zen Cart Check FAIL on {0} Checked URL:{1}. Zen Cart Version:{3}. {2}".format(host,url,reason,release))
   sys.exit(2)		# Nagios status = Critical iff exit code = 2.

if __name__ == '__main__':
    main()