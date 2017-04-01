# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
from bs4 import BeautifulSoup


# --------------- Helpers that build all of the responses ---------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# ------------ Functions ---------------

def clean_text(text):
    """ this function is used to clean the space character returned from
    td.span.text"""
    return text.replace(u'\xa0', '')


def construct_message(time, unit, direction):
    """ take input time, unit, and direction, then return a meaningful
    message"""
    return time + ' ' + unit


def url_query(state, city, line, stop, direction):
    """ construct the query for url based on provided bus information """
    # hard-coded for now
    return "a=omnitrans&r=8&s=5151"


def get_next_bus(state, city, line, stop, direction):
    """ get bus schedule based on input parameters. Return bus schedules
    in a list."""
    query = url_query(state, city, line, stop, direction)
    url = 'https://www.nextbus.com/predictor/adaPrediction.jsp?' + query
    response = requests.get(url)
    return_messages = []
    prediction_table = None

    soup = BeautifulSoup(response.text, 'html.parser')
    for table in soup.find_all('table'):
        # class is a multivalue tag in html, which is returned as list in soup
        if table['class'][0] == 'adaPredictionTable':
            # retrive the Prediction Table
            prediction_table = table
            break

    if prediction_table is None:
        return return_messages
    else:
        next_buses = prediction_table.find_all('tr')

    for row in next_buses:
        time, unit = [clean_text(td.span.text) for td in row.find_all('td')[:2]]
        return_messages.append(construct_message(time, unit, direction))

    return return_messages


# ------------- Skills -------------------
def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "welcome"
    speech_output = "Welcome to MyBus. Please tell me which bus to track."

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me which bus to track."
    should_end_session = False

    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output,
                                                   reprompt_text, should_end_session))


def get_bus_estimate_from_session(intent, session):
    """ user provides bus information for tracking """
    # for now just hard-coded and assume my own bus
    session_attributes = {}
    reprompt_text = None

    bus_estimate = get_next_bus(state="ca", city="redlands", line="8",
                                stop="5151", direction="eb")
    if not bus_estimate:
        speech_output = "There is no bus scheduled based on your request. " +\
                        "Please try again later."
    else:
        speech_output = "Your next bus is coming in {}".format(' and '.join(bus_estimate))

    should_end_session = True

    return build_response(session_attributes,
                          build_speechlet_response(intent['name'], speech_output,
                                                   reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying MyBus. Have a nice day!"
    should_end_session = True
    return build_response({},
                          build_speechlet_response(card_title, speech_output,
                                                   None, should_end_session))

# ------------ Events handlers ------------


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ called when the user specifies an intent for this skill """
    # only "GetBusEstimate" for now
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to the skill handlers
    if intent_name == "GetBusEstimate":
        return get_bus_estimate_from_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# ------------ Main handler -----------------
def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


if __name__ == "__main__":
    import json
    event = json.loads("""{
              "session": {
                "new": false,
                "sessionId": "amzn1.echo-api.session.[unique-value-here]",
                "attributes": {},
                "user": {
                  "userId": "amzn1.ask.account.[unique-value-here]"
                },
                "application": {
                  "applicationId": "amzn1.ask.skill.[unique-value-here]"
                }
              },
              "version": "1.0",
              "request": {
                "locale": "en-US",
                "timestamp": "2016-10-27T21:06:28Z",
                "type": "IntentRequest",
                "requestId": "amzn1.echo-api.request.[unique-value-here]",
                "intent": {
                  "slots": {},
                  "name": "GetBusEstimate"
                }
              },
              "context": {
                "AudioPlayer": {
                  "playerActivity": "IDLE"
                },
                "System": {
                  "device": {
                    "supportedInterfaces": {
                      "AudioPlayer": {}
                    }
                  },
                  "application": {
                    "applicationId": "amzn1.ask.skill.[unique-value-here]"
                  },
                  "user": {
                    "userId": "amzn1.ask.account.[unique-value-here]"
                  }
                }
              }
            }""")

    lambda_handler(event, None)
