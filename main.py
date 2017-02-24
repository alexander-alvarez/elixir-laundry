import json
import logging
import os
import redis
import sys

from flask import Flask, request, make_response
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Call

# constants
NOTIFICATION_ROUTE = '/notify_status'
USER_CALL_ID_KEY = 'user_call_id'

# environment variables
user_phone_number = os.environ.get('USER_PHONE_NUMBER')
destination_phone_number = os.environ.get('DESTINATION_PHONE_NUMBER')
handle_call_url = os.environ.get('CALLBACK_API_HOST') + NOTIFICATION_ROUTE
account = os.environ.get('TWILIO_ACCOUNT_SID')
token = os.environ.get('TWILIO_AUTH_TOKEN')


app = Flask(__name__)
cache = redis.StrictRedis(host='localhost', port=6379)

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
    app.logger.info('Call started {}'.format(user_call.name))
    cache.set(USER_CALL_ID_KEY, user_call.name)
    return make_response('', 200)


@app.route(NOTIFICATION_ROUTE, methods=['POST'])
def notify():
    data = request.form.copy()
    call_sid = data.get('CallSid')
    call_status = data.get('CallStatus')
    destination_number = data.get('Called')
    response = make_response('status:{0};{1}'.format(call_status, call_sid), 200)

    if call_sid == cache.get(USER_CALL_ID_KEY):
        if call_status == Call.COMPLETED:
            app.logger.info('Program execution finished')
        elif call_status == Call.IN_PROGRESS:
            # then call destination phone in the allotted time every 5 seconds until one picks up
            app.logger.info('Starting process of calling destination now that user is on the line')
            pass
        else:
            return response
    elif destination_number == destination_phone_number:
        # if busy, cancel call and
        if call_status == Call.IN_PROGRESS:
            # join destination call to user call
            # abort all other dialing calls
            pass

    app.logger.info(json.dumps(data))
    return response

if __name__ == "__main__":
    # docker run -d -p 6379:6379 redis
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    err_handler = logging.StreamHandler(sys.stderr)
    err_handler.setLevel(logging.ERROR)
    app.logger.addHandler(stdout_handler)
    app.logger.addHandler(err_handler)

    app.run('0.0.0.0', 8000, debug=True)
