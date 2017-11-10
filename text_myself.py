#! python3

"""
Simple module that uses Twilio to send SMS messages to yourself. This module was
inspired by Al Sweigart's "Automate the Boring Stuff" (Project: “Just Text Me”
Module in Chapter 16).

Possible areas for future development:

    - Use "backoff" to more elegantly handle delayed collection of SMS message
        send status after posting initial send request.
    - Support SMS messages with media (e.g. images).
    - Allow usage beyond restrictions of Twilio free account
        (e.g. send to/from multiple phone numbers).
"""

# std
import argparse
from configparser import ConfigParser
import logging
import os
import time

# 3rd party
from twilio.rest import Client

# logging
LOG_FILEPATH = os.path.expanduser('~') + '/dev/logs.txt'
logging.basicConfig(filename=LOG_FILEPATH, level=logging.INFO)
LOGGER = logging.getLogger('text_myself')

# global constants
CONFIG_FILEPATH = os.path.expanduser('~') + '/dev/py_config.ini'

def get_sms_credentials(config_filepath=None):
    '''
    Fetches Twilio credentials from a Config .ini file stored locally.

    Args:
        config_filepath: String that is the full path on the local machine
            to a .ini file (in the style of ConfigParser) that contains
            Twilio API credentials.

    Returns:
        credentials: Dictionary containing the `ACCOUNT_SID` and `AUTH_TOKEN`
            for the Twilio API.
    '''
    if not config_filepath:
        config_filepath = CONFIG_FILEPATH
    if not os.path.exists(CONFIG_FILEPATH):
        raise ValueError('Path provided for config file does not exist')

    config = ConfigParser()
    config.read(config_filepath)
    credentials = {}
    try:
        credentials['ACCOUNT_SID'] = config['Twilio']['ACCOUNT_SID']
        credentials['AUTH_TOKEN'] = config['Twilio']['AUTH_TOKEN']
        credentials['FROM_PHONE_NUMBER'] = config['Twilio']['FROM_PHONE_NUMBER']
        credentials['TO_PHONE_NUMBER'] = config['General']['TO_PHONE_NUMBER']
    except Exception as e:
        print(config_filepath)
        print('An exception occurred when reading config file: %s' % e)

    return credentials

def send_sms_message(message=None, credentials=None):
    '''
    Sends a simple, text-only SMS message using the Twilio REST client.

    Args:
        message: String up to 1.6k in length. This is the message that will be
            sent via SMS.
        credentials: Dict containing keys `ACCOUNT_SID` and `AUTH_TOKEN` that
            are associated with an active Twilio user.

    Returns:
        sms_message_status: The function allows 10 seconds to pass after sending
            a message then polls the API to fetch updated send status.
    '''
    if not message:
        raise ValueError('No message found.')

    if not credentials:
        raise ValueError('No API credentials found.')

    client = Client(credentials['ACCOUNT_SID'], credentials['AUTH_TOKEN'])
    sms_status = None

    try:
        sms_message = client.messages.create(
            to=credentials['TO_PHONE_NUMBER'],
            body=message,
            from_=credentials['FROM_PHONE_NUMBER']
        )
        # pause for 10 seconds then collect send status
        time.sleep(10)
        sms_message_updated = client.messages.get(sms_message.sid).fetch()
        sms_status = sms_message_updated.status

    except Exception as e:
        sms_status = 'send_error'
        print('There was a problem when sending SMS message: %s' % e)

    return sms_status

def send(message=None):
    '''
    Run method for module.

    Args:
        message: String. It is possible to run this method via another script
            by importing as a module.
        -m or --message: Optional CLI arguments can also be passed to use this
            script in a stand-alone fashion.
    '''
    if not message:
        args = argparse.ArgumentParser()
        args.add_argument('-m', '--message', dest='message', required=False,
                          nargs='*', help='Enter the message that you want to \
have sent. Up to 1.6k characters is supported.')
        message = ' '.join(args.parse_args().message)

    try:
        credentials = get_sms_credentials()
        message_status = send_sms_message(message=message, credentials=credentials)
        message_short_ver = message[:30] + '...'

        if message_status == 'delivered':
            LOGGER.info('text_myself.py: Successfully sent message: "%s"',
                        message_short_ver)
        else:
            LOGGER.warning('Issue sending message: "%s". Message status: %s',
                           message_short_ver, message_status)
    except Exception as e:
        print('Error sending message: %s' % e)
        LOGGER.warning('Error sending message: %s', e)


if __name__ == '__main__':
    send()
