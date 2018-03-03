#! /usr/bin/env python3

import sys
import datetime
import time
import logging
import argparse
import requests
# import psycopg2
import json
import tweepy
from bastoebot.disruption import Disruption
from bastoebot.disruption_message import DisruptionMessage

def get_api(cfg):
    auth = tweepy.OAuthHandler(cfg.get("consumer_key", "abc"), cfg.get("consumer_secret", "def"))
    auth.set_access_token(cfg.get("access_token", "ghi"), cfg.get("access_token_secret", "jkl"))
    return tweepy.API(auth)

def tweet(configuration, disruption, api):
    LIMIT = 270
    FILL = 6
    location = disruption.text_from
    if disruption.text_to is not None and disruption.text_to != disruption.text_from:
        location += "–{}".format(disruption.text_to)
    length = len(location)
    heading = disruption.title
    length += len(heading)
    valid_to = "bis vsl. {}".format(datetime.datetime.strftime(disruption.end_date, "%d.%m. %H:%M"))
    length += len(valid_to)
    last_update = "Stand {}".format(datetime.datetime.strftime(disruption.mod_date, "%d.%m. %H:%M"))
    length += len(last_update)
    text = ""
    if len(disruption.messages) > 0:
        message = disruption.messages[-1].text
        remaining = LIMIT - length - FILL
        if remaining > len(text):
            message = "{}…".format(message[0:(remaining - 1)])
        text = "{}: {} {} {}, {}".format(location, heading, message, valid_to, last_update)
    else:
        text = "{}: {} {}, {}".format(location, heading, valid_to, last_update)

    logging.info("Tweet ({} characters): '{}'".format(len(text), text))
    if not configuration["dry_run"]:
        status = api.update_status(status=text)
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log-level", type=str, default="INFO", help="log level")
    parser.add_argument("-D", "--dry-run", action="store_true", default=False, help="dryrun mode, don't tweet")
    parser.add_argument("-c", "--config", help="configuration file", type=argparse.FileType("r"))
    parser.add_argument("--start", type=int, default=0, help="minimum index in the response list by the HAFAS HIM API")
    parser.add_argument("--stop", type=int, default=100, help="maximum index in the response list by the HAFAS HIM API")
    args = parser.parse_args()

    # log level
    numeric_log_level = getattr(logging, args.log_level.upper())
    if not isinstance(numeric_log_level, int):
        raise ValueError("Invalid log level {}".format(args.log_level.upper()))
    logging.basicConfig(level=numeric_log_level)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    configuration = json.load(args.config)
    configuration["dry_run"] = args.dry_run
    twitter_api = get_api(configuration)
    
    API_URL = "http://db-livemaps.hafas.de/bin/mgate.exe"
    HEADERS = {"User-Agent": "BastoeBot", "Content-type": "application/x-www-form-urlencoded"}
    
    params = {"ver":"1.15","lang":"deu","auth":{"type":"AID","aid":"hf7mcf9bv3nv8g5f"},"client":{"id":"DBZUGRADARNETZ","type":"WEB","name":"webapp","v":"0.1.0"},"formatted":False,"svcReqL":[{"meth":"HimGeoPos","req":{"prio":100,"maxNum":5000,"getPolyLine":True, "rect": {"llCrd":{"x":5500000.0,"y":47000000.0},"urCrd":{"x":15400000.0,"y":55000000.0}},"dateB":"20180303","timeB":"160000","dateE":"20180303","timeE":"235900","onlyHimId":False,"himFltrL":[{"type":"HIMCAT","mode":"INC","value":"0"},{"type":"PROD","mode":"INC","value":1023}]},"cfg":{"cfgGrpL":[],"cfgHash":"i74dckao7PmBwS0rbk0p"}}],"ext":"DBNETZZUGRADAR.2"}
    data = json.dumps(params)
    
    r = requests.post(API_URL, data=data, headers=HEADERS)
    
    response = r.json()["svcResL"][0]["res"]["common"]
    locL = response["locL"]
    himMsgEdgeL = response["himMsgEdgeL"]
    himL = response["himL"]
    
    disruptions = []
    
    for entry in himL:
        disruptions.append(Disruption(entry, himMsgEdgeL, locL))
    
    for idx in range(0, len(disruptions)):
        if idx >= args.start and idx <= args.stop:
            tweet(configuration, disruptions[idx], twitter_api)
