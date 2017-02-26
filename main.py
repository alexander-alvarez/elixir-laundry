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
DEST_CALL_ID_KEY = 'dest_call_id'

# environment variables
user_phone_number = os.environ.get('USER_PHONE_NUMBER')
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
                                    url="https://handler.twilio.com/twiml/EHbbeae53391ad39e7585cd3c604f68420"
                                    )
    app.logger.info('Call started {}'.format(user_call.name))
    cache.set(USER_CALL_ID_KEY, user_call.name)
    return make_response('success', 200)


@app.route('/call_dest/<destination_number>')
def call_dest(destination_number):
    # call user phone first, and wait for pickup.
    user_call = client.calls.create(to=destination_number,
                                    from_=user_phone_number,
                                    url="https://handler.twilio.com/twiml/EHbbeae53391ad39e7585cd3c604f68420",
                                    status_callback=handle_call_url,
                                    status_events=['initiated', 'ringing', 'answered', 'completed']
                                    )
    app.logger.info('Call started {}'.format(user_call.name))
    cache.lpush(DEST_CALL_ID_KEY, user_call.name)
    return make_response('called {0}'.format(str(destination_number)), 200)


# TODO dial tone #3

@app.route(NOTIFICATION_ROUTE, methods=['POST'])
def notify():
    data = request.form.copy()
    call_sid = data.get('CallSid')
    call_status = data.get('CallStatus')
    machine = data.get('AnsweredBy') == 'machine' # not sure this is API
    response = make_response('status:{0};{1}'.format(call_status, call_sid), 200)

    # update status in cache
    cache.set(call_sid, call_status)

    # if busy, cancel call and
    if call_status == Call.IN_PROGRESS and not machine:
        # abort all other dialing calls
        call_sids = cache.lrange(DEST_CALL_ID_KEY, 0, -1)
        for key in call_sids:
            # hang up all but current call
            if key != call_sid:
                try:
                    call_to_hangup_status = cache.get(call_sid)
                    if call_to_hangup_status not in {Call.CANCELED, Call.COMPLETED}:
                        client.calls.hangup(key)
                except Exception:
                    app.logger.info('An error occured cancelling call {0}, with status {1}'.format(
                        key, cache.get(key)
                    )
                    )

    app.logger.info(json.dumps(data))
    return response

@app.route('/reset', methods=['GET'])
def reset():
    """
        Clears the cache.

    :return: HTTP 200
    """
    response = make_response('cache cleared', 200)
    cache.flushall()
    return response


if __name__ == "__main__":
    # docker run -d -p 6379:6379 redis
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    err_handler = logging.StreamHandler(sys.stderr)
    err_handler.setLevel(logging.ERROR)
    app.logger.addHandler(stdout_handler)
    app.logger.addHandler(err_handler)

    app.run('0.0.0.0', 8000, debug=True, threaded=True)
