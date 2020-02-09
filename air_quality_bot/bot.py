import logging
import random
from argparse import ArgumentParser
import requests

import os
from flask import Flask, request
from flask_restful import Api
from utils import log
from utils.abstract_classes import Bot
from utils.dict_query import DictQuery
import datetime
import random
import pandas as pd
import numpy as np
from word2number import w2n


from rasa.nlu.model import Interpreter, Metadata

app = Flask(__name__)
api = Api(app)
BOT_NAME = "air_quality_bot"
VERSION = log.get_short_git_version()
BRANCH = log.get_git_branch()

logger = logging.getLogger(__name__)

parser = ArgumentParser()
parser.add_argument('-p', "--port", type=int, default=5130)
parser.add_argument('-l', '--logfile', type=str, default='logs/' + BOT_NAME + '.log')
parser.add_argument('-cv', '--console-verbosity', default='info', help='Console logging verbosity')
parser.add_argument('-fv', '--file-verbosity', default='debug', help='File logging verbosity')


## DATASET PARAMS
DATASET_FILE_NAME = "edi_air_quality.csv"
DATASET_PATH = f"data/{DATASET_FILE_NAME}"

dataset = pd.read_csv(DATASET_PATH)
# convert str to int in dataset
for column in dataset.columns:
    if column != "date":
        dataset[column] = pd.to_numeric(dataset[column], errors='coerce')


## RASA PARAMS
example_utterance = u"how great will air be next week"
MODEL_NAME = "nlu-20200209-185009"
MODEL = f"models/{MODEL_NAME}/nlu"
# loading the model from one directory or zip file
interpreter = Interpreter.load(MODEL)


## WAGI API PARAMS
API_KEY = "dc7cf06b49047ee83091c9c350abcf80db6fbd43"
API_URL = f"https://api.waqi.info/feed/edinburgh/?token={API_KEY}"


def row_is_between_dates(row, low_date, up_date):

    date_row = row["date"].split("/")
    true_date_row = datetime.date(int(date_row[0]), int(date_row[1]), int(date_row[2]))

    return true_date_row <= up_date and true_date_row > low_date

class AirQualityBot(Bot):
    def __init__(self, **kwargs):
        # Warning: the init method will be called every time before the post() method
        # Don't use it to initialise or load files.
        # We will use kwargs to specify already initialised objects that are required to the bot
        super(AirQualityBot, self).__init__(bot_name=BOT_NAME)
        self.greetings = [
        "It's sunny",
        "It's windy",
        "Innae good time to gettout innit ?"
        ]

        self.intents = [
        "air_quality_forecast",
        "air_quality_today",
        "air_quality_historical"
        ]

        self.entities = {
        "good":["good", "great", "nice"],
        "hierarchy_number":["next","future"] + [str(i) for i in range(10)],
        "time_measures":["day","week","month","year"]
        }

    def get(self):
        pass


    def get_response_from_rasa_interpretation(self, interpretation):
        intent = interpretation['intent']['name']

        returned_response = "I did not get that. Could you repeat ?"

        if intent == "air_quality_today":
            r = requests.get(url=API_URL)
            response = r.json()

            returned_response = f"""
            Today's air is as follows:
            - h: {response['data']['iaqi']['h']['v']}
            - no2: {response['data']['iaqi']['no2']['v']}
            - o3: {response['data']['iaqi']['o3']['v']}
            - p: {response['data']['iaqi']['p']['v']}
            - pm10: {response['data']['iaqi']['pm10']['v']}
            - pm25: {response['data']['iaqi']['pm25']['v']}
            - so2: {response['data']['iaqi']['so2']['v']}
            """

        elif intent == "air_quality_historical":

            returned_response = ""

            number = None
            hierarchy_number = None
            time_measures = None
            for entity in interpretation['entities']:

                if entity["entity"] == "hierarchy_number":
                    hierarchy_number = entity["value"]

                elif entity["entity"] == "time_measures":
                    time_measures = entity["value"]

                elif entity["entity"] == "number":
                    number = entity["value"]

            if number is None and hierarchy_number is None and time_measures is None:
                returned_response = "Query not fully understood, returning last week data by default:"
                hierarchy_number = "last"
                time_measures = "week"

            # count the number of unit of time measures
            counter = 1
            # convert the unit of time measures as days
            time_measure_factor = 1

            if (time_measures[0:4] == "week"):
                time_measure_factor = 7
            elif (time_measures[0:5] == "month"):
                time_measure_factor = 30
            elif (time_measures[0:4] == "year"):
                time_measure_factor = 365

            # e.g. last week
            if (hierarchy_number == "last" and number is None):
                counter = 1    
            # e.g last 2 weeks
            elif (hierarchy_number == "last" and number is not None):
                try:
                    counter = int(number)
                except:
                    counter = w2n.word_to_num(number)
            elif (number is not None):
                try:
                    counter = number
                except:
                    counter = w2n.word_to_num(number)
            # e.g one month ago (we then check the date one month ago and move 7 days ahead)
            if (hierarchy_number != "last"):

                d_up = datetime.date.today() - datetime.timedelta(days=counter*time_measure_factor) + datetime.timedelta(days = 7)

            else:

                d_up = datetime.date.today() # to switch for interval of time

            d_down = d_up - datetime.timedelta(days=counter*time_measure_factor)

            rows_of_dataset = dataset[dataset.apply(lambda x: row_is_between_dates(x, low_date = d_down, up_date = d_up), axis=1)]

            returned_response+=f"""
            \n
            Air quality of the last {counter*time_measure_factor} days was like this:

            """

            for column in dataset.columns:
                if column != "date":
                    returned_response += f"""
                    - The average value of {column} is {dataset[column].mean()}
                    """

        return returned_response


    def post(self):
        # This method will be executed for every POST request received by the server on the
        # "/" endpoint (see below 'add_resource')

        # We assume that the body of the incoming request is formatted as JSON (i.e., its Content-Type is JSON)
        # We parse the JSON content and we obtain a dictionary object
        request_data = request.get_json(force=True)

        # We wrap the resulting dictionary in a custom object that allows data access via dot-notation
        request_data = DictQuery(request_data)

        # We extract several information from the state
        user_utterance = request_data.get("current_state.state.nlu.annotations.processed_text")
        last_bot = request_data.get("current_state.state.last_bot")

        logger.info("------- Turn info ----------")
        logger.info("User utterance: {}".format(user_utterance))
        logger.info("Last bot: {}".format(last_bot))
        logger.info("---------------------------")
        logger.info("Sending to rasa interpreter...")

        # parsing the utterance
        interpretation = interpreter.parse(user_utterance)

        response = self.get_response_from_rasa_interpretation(interpretation)

        # the 'result' member is intended as the actual response of the bot
        self.response.result = response

        print(f"Answer: {response}")

        # we store in the dictionary 'bot_params' the current time. Remember that this information will be stored
        # in the database only if the bot is selected
        self.response.bot_params["time"] = str(datetime.datetime.now())

        # The response generated by the bot is always considered as a list (we allow a bot to generate multiple response
        # objects for the same turn). Here we create a singleton list with the response in JSON format
        return [self.response.toJSON()]





if __name__ == "__main__":
    args = parser.parse_args()

    if not os.path.exists("logs/"):
        os.makedirs("logs/")

    log.set_logger_params(BOT_NAME + '-' + BRANCH, logfile=args.logfile,
    file_level=args.file_verbosity, console_level=args.console_verbosity)

    api.add_resource(AirQualityBot, "/")

    app.run(host="0.0.0.0", port=args.port)
