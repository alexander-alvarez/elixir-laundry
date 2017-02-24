import os

from twilio.rest import TwilioRestClient

user_phone_number = os.environ.get('USER_PHONE_NUMBER')
destination_phone_number = os.environ.get('DESTINATION_PHONE_NUMBER')

account = os.environ.get('TWILIO_ACCOUNT_SID')
token = os.environ.get('TWILIO_AUTH_TOKEN')
client = TwilioRestClient(account, token)




# call user phone first, and wait for pickup.


# then call destination phone in the allotted time every 5 seconds until one picks up

# then join destination call to user call


#  and stop any other background calls, and prevent creating more calls



