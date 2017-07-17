# coding=utf-8
import argparse
import os
import sys
import time
import traceback
from decimal import Decimal
from httplib import BadStatusLine
from urllib2 import URLError

import modules.Configuration as Config
import modules.Data as Data
import modules.Lending as Lending
import modules.MaxToLend as MaxToLend
from modules.Logger import Logger
from modules.Poloniex import Poloniex, PoloniexApiError
import modules.PluginsManager as PluginsManager


try:
    open('lendingbot_my.py', 'r')
except IOError:
    os.chdir(os.path.dirname(sys.argv[0]))  # Allow relative paths

"""
parser = argparse.ArgumentParser()  # Start args.
parser.add_argument("-cfg", "--config", help="Location of custom configuration file, overrides settings below")
parser.add_argument("-dry", "--dryrun", help="Make pretend orders", action="store_true")
args = parser.parse_args()  # End args.
# Start handling args.
dry_run = bool(args.dryrun)
if args.config:
    config_location = args.config
else:
    config_location = 'default.cfg'
# End handling args.
"""

dry_run = False
config_location = 'default.cfg'
Config.init(config_location)
# Config format: Config.get(category, option, default_value=False, lower_limit=False, upper_limit=False)
# A default_value "None" means that the option is required and the bot will not run without it.
# Do not use lower or upper limit on any config options which are not numbers.
# Define the variable from the option in the module where you use it.
output_currency = Config.get('BOT', 'outputCurrency', 'BTC')
end_date = Config.get('BOT', 'endDate')
json_output_enabled = Config.has_option('BOT', 'jsonfile') and Config.has_option('BOT', 'jsonlogsize')

username = sys.argv[6]

print("JSON file Name:")
print(Config.get('BOT', 'jsonfile', '') + username + '_botlog.json')
log = Logger(Config.get('BOT', 'jsonfile', '') + username + '_botlog.json', Decimal(Config.get('BOT', 'jsonlogsize', -1)))
#api = Poloniex(Config.get("API", "apikey", None), Config.get("API", "secret", None))

print sys.argv[1]
print sys.argv[2]
apikey = sys.argv[1]
secret = sys.argv[2]
api = Poloniex(apikey, secret)
MaxToLend.init(Config, log)
Data.init(api, log)
Config.init(config_location, Data)
notify_conf = Config.get_notification_config()
if Config.has_option('BOT', 'analyseCurrencies'):
    from modules.MarketAnalysis import MarketAnalysis
    # Analysis.init(Config, api, Data)
    analysis = MarketAnalysis(Config, api)
    analysis.run()
else:
    analysis = None
Lending.init(Config, api, log, Data, MaxToLend, dry_run, analysis, notify_conf)

# load plugins
PluginsManager.init(Config, api, log, notify_conf)

print 'Welcome to Poloniex Lending Bot'


# Configure web server

web_server_enabled = Config.getboolean('BOT', 'startWebServer')
if web_server_enabled:  # Run web server
    import modules.WebServer as WebServer
    WebServer.initialize_web_server(Config)

mr = Decimal(sys.argv[3])
mrl = Decimal(sys.argv[4])
duration = sys.argv[5]

username = sys.argv[6]

Lending.setParam(mr, mrl, duration)
try:
    while True:
        try:
            Data.update_conversion_rates(output_currency, json_output_enabled)
            PluginsManager.before_lending()
            Lending.transfer_balances()
            Lending.cancel_all()
#            Lending.setParam(0.5, 0.2, 60)
            print "OKOK"
            Lending.lend_all()
            PluginsManager.after_lending()
            log.refreshStatus(Data.stringify_total_lent(*Data.get_total_lent()),
                              Data.get_max_duration(end_date, "status"))
            log.persistStatus()
            sys.stdout.flush()
            print "OOOOOO"
            time.sleep(Lending.get_sleep_time())
            print "KKKKKK"
        except KeyboardInterrupt:
            # allow existing the main bot loop
            raise
        except Exception as ex:
            log.log_error(ex.message)
            log.persistStatus()
            if 'Invalid API key' in ex.message:
                print "!!! Troubleshooting !!!"
                print "Are your API keys correct? No quotation. Just plain keys."
                exit(1)
            elif 'Nonce must be greater' in ex.message:
                print "!!! Troubleshooting !!!"
                print "Are you reusing the API key in multiple applications? Use a unique key for every application."
                exit(1)
            elif 'Permission denied' in ex.message:
                print "!!! Troubleshooting !!!"
                print "Are you using IP filter on the key? Maybe your IP changed?"
                exit(1)
            elif 'timed out' in ex.message:
                print "Timed out, will retry in " + str(Lending.get_sleep_time()) + "sec"
            elif isinstance(ex, BadStatusLine):
                print "Caught BadStatusLine exception from Poloniex, ignoring."
            elif 'HTTP Error 429' in ex.message:
                additional_sleep = max(130.0-Lending.get_sleep_time(), 0)
                print "IP has been banned for 120 seconds due too many requests. Sleeping for " + str(additional_sleep+Lending.get_sleep_time()) + " seconds."
                time.sleep(additional_sleep)
            # Ignore all 5xx errors (server error) as we can't do anything about it (https://httpstatuses.com/)
            elif isinstance(ex, URLError):
                print "Caught {0} from Poloniex, ignoring.".format(ex.message)
            elif isinstance(ex, PoloniexApiError):
                print "Caught {0} reading from Poloniex API, ignoring.".format(ex.message)
            else:
                print traceback.format_exc()
                print "Unhandled error, please open a Github issue so we can fix it!"
                log.notify("{0}\n-------\n{1}".format(ex, traceback.format_exc()), notify_conf)
            sys.stdout.flush()
            time.sleep(Lending.get_sleep_time())
            pass

except KeyboardInterrupt:
    if web_server_enabled:
        WebServer.stop_web_server()
    PluginsManager.on_bot_exit()
    log.log('bye')
    print 'bye'
    os._exit(0)  # Ad-hoc solution in place of 'exit(0)' TODO: Find out why non-daemon thread(s) are hanging on exit
