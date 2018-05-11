from urllib.request import Request, urlopen
import base64
import xmltodict
import requests
import time
import traceback
import argparse
from collections import OrderedDict


def run(args):

    listeners_xml_url = "{}/admin.cgi?sid={}&mode=viewxml&page=3".format(args.url_shoutcast, args.sid)
    stats_xml_url = "{}/admin.cgi?sid={}&mode=viewxml&page=5".format(args.url_shoutcast, args.sid)

    print("Listeners XML: {}".format(listeners_xml_url))
    print("Stats XML: {}".format(stats_xml_url))

    req_listeners = Request(listeners_xml_url)
    req_listeners.add_header('Authorization', b'Basic ' + base64.b64encode(str.encode(args.user) + b':' + str.encode(args.password)))

    req_stats = Request(stats_xml_url)
    req_stats.add_header('Authorization', b'Basic ' + base64.b64encode(str.encode(args.user) + b':' + str.encode(args.password)))

    while True:

        songtitle = ""
        try:
            with urlopen(req_stats) as f:
                stats_data = f.read()

            stats_xml = xmltodict.parse(stats_data)

            if stats_xml['SHOUTCASTSERVER']['SONGMETADATA'] is not None and 'TIT2' in stats_xml['SHOUTCASTSERVER']['SONGMETADATA']:
                songtitle = stats_xml['SHOUTCASTSERVER']['SONGMETADATA']['TIT2']

        except Exception as e:
            traceback.print_exc()

            songtitle = "STREAMING"
            print("Failed to get song title.")

        print("Songtitle: {}".format(songtitle))

        try:
            file = urlopen(req_listeners)
            data = file.read()
            file.close()
            xml = xmltodict.parse(data)

            current_sessions = []

            if xml['SHOUTCASTSERVER']['LISTENERS'] is not None:
                for key, value in xml['SHOUTCASTSERVER']['LISTENERS'].items():

                    if type(value) is list:
                        for listener in value:
                            process_listener(args, current_sessions, listener, songtitle)

                    elif type(value) is OrderedDict:
                        process_listener(args, current_sessions, value, songtitle)

                    else:
                        print("ERROR: Can't process listener of type {}. {}".format(type(value), value))

                print("Currently {} listeners online".format(len(current_sessions)))

            else:
                print("No listeners in shoutcast!")
            time.sleep(300)

        except Exception:
            traceback.print_exc()

            print("Failed. \nXML: {}\nData:".format(xml, data))
            time.sleep(1)


def process_listener(args, current_sessions, listener, songtitle):

    current_sessions.append(listener['UID'])

    payload = {
        'v': 1,
        'tid': args.tracking_id,
        'cid': listener['UID'],
        'uip': listener['HOSTNAME'],
        'ua': listener['USERAGENT'],
        't': 'pageview',
        'dh': args.domain,
        'dp': args.page_path,
        'dt': songtitle
    }

    requests.post("http://www.google-analytics.com/collect", data=payload)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--tracking_id', help='Google Analytics Tracking ID', required=True)
    parser.add_argument('--url_shoutcast', help='Shoutcast root URL (ie: http://shoutcastserv.com:8000', required=True)
    parser.add_argument('--sid', help='Stream ID (ie: 1)', required=True)
    parser.add_argument('--user', help='Shoutcast Admin username', default='admin')
    parser.add_argument('--password', help='Shoutcast Admin password', required=True)
    parser.add_argument('--page_path', help='The listener will appear as a visit to this path', default='/streaming.mp3')
    parser.add_argument('--page_name', help='Page name where the listener will be registered as a visit', default='Streaming')
    parser.add_argument('--domain', help='Streaming domain', default='streaming.com')
    args = parser.parse_args()

    run(args)
