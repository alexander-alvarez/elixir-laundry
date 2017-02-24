import json
import logging
import os

from flask import Flask, request
from twilio.rest import TwilioRestClient

logger = logging.getLogger(__name__)

app = Flask(__name__)

NOTIFICATION_ROUTE = '/notify_status'

user_phone_number = os.environ.get('USER_PHONE_NUMBER')
destination_phone_number = os.environ.get('DESTINATION_PHONE_NUMBER')
handle_call_url = os.environ.get('CALLBACK_API_ENDPOINT') + NOTIFICATION_ROUTE

account = os.environ.get('TWILIO_ACCOUNT_SID')
token = os.environ.get('TWILIO_AUTH_TOKEN')
client = TwilioRestClient(account, token)

user_call_id = None

@app.route('/call_user')
def call_user():
    # call user phone first, and wait for pickup.
    user_call = client.calls.create(to=user_phone_number,
                                    from_=user_phone_number,
                                    url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient",
                                    status_callback=handle_call_url,
                                    status_events=['initiated', 'ringing', 'answered', 'completed']
                                    )
    logger.info('Call started {}'.format(user_call.id_key))


@app.route(NOTIFICATION_ROUTE, options=['POST'])
def notify():
    data = request.get_json()
    logger.info(json.dumps(data))

# then call destination phone in the allotted time every 5 seconds until one picks up

# then join destination call to user call


#  and stop any other background calls, and prevent creating more calls
if __name__ == "__main__":
    app.run('0.0.0.0', 80)
