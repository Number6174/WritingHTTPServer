# SPDX-FileCopyrightText: 2021 Number6174
# SPDX-License-Identifier: Apache-2.0

import http.server
from urllib.parse import urlparse
from urllib.parse import parse_qs
import datetime
import json
import logging
from dateutil.parser import parse
import pynput
import threading
import time

class WritingHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_error(self, format, *args):
        global logger
        logger.error(format%args)
        
    def log_message(self, format, *args):
        global logger
        logger.debug(format%args)

    def log_event(self, format, *args):
        global logger
        logger.info(format%args)

    def do_GET(self):
        # Handle the request
        url = urlparse(self.path)
        if url.path == '/':
            self.path = 'control_panel.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif url.path == '/favicon.ico':
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif url.path.startswith('/api'):
            self.handle_api()
        elif url.path == '/event':
            self.handle_event()
        elif url.path =='/keypress':
            self.handle_keypress()
        elif url.path == '/write':
            self.handle_write()
        elif url.path == '/timer':
            self.handle_timer()
        else:
            self.log_message("Ignoring request to " + self.path)
            self.send_error(404)

    def do_PUT(self):
        # Acquire the PUT data
        content_length = int(self.headers['Content-Length'])
        raw_data = self.rfile.read(content_length)
        data = json.loads(raw_data, parse_float=float, parse_int=int)

        url = urlparse(self.path)
        if url.path == '/api/configwriter/timer_data':
            with open('timer_data.json', 'w') as f:
                json.dump(data, f, indent=4)
            self.log_message('Updated timer_data.json')
        elif url.path == '/api/configwriter/config':
            self.log_message("About to update config.json with %s", data)
            with open('config.json', 'r') as f:
                existing = json.load(f)

            # Copy the two settings we don't allow changing by the control panel
            data['host'] = existing['host']
            data['port'] = existing['port']
            with open('config.json', 'w') as f:
                json.dump(data, f, indent=4)
            
            # Reload config for rest of program
            global config
            config = readConfig('config.json')
            self.log_message('Updated config.json')
        else:
            self.log_message("Ignoring PUT to " + self.path)
            self.send_error(400)
            return

        self.success_response()

    def success_response(self):
        # Write response
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        body = f"Success"
        self.wfile.write(bytes(body, "utf8"))

    def handle_api(self):
        url = urlparse(self.path)
        if url.path == '/api/timer':
            # Open timer_data.json
            with open('timer_data.json') as f:
                data = json.load(f)
                self.log_message("/api/timer: " + json.dumps(data))
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(data, indent=4), "utf8"))
            return
        elif url.path == '/api/config':
            # Open timer_data.json
            with open('config.json') as f:
                data = json.load(f)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(data, indent=4), "utf8"))
            return
        elif url.path == '/api/events':
            with open('logs/events.log') as f:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(bytes(f.read(), 'utf-8'))
            return
        elif url.path == '/api/twitch/id_to_name':
            query = parse_qs(urlparse(self.path).query)
            if 'id' not in query:
                self.send_error(400)
                return
            response = twitch_id_to_name_cached(query['id'][0])
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(bytes(response, "utf8"))
            return
        elif url.path == '/api/version':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(version_string(), "utf8"))
            return
        self.log_message('Unknown API call ' + url.path)
        self.send_error(400)

    def handle_event(self):
        # Extract query
        query = parse_qs(urlparse(self.path).query)

        global config

        if 'train' in query:
            # Some kind of hype train event
            type = query['train'][0]
            if type == 'start':
                self.log_event('Hype Train Start')
            elif type == 'end':
                sub_conductor_id = query['sub_conductor'][0]
                sub_conductor = twitch_id_to_name_cached(sub_conductor_id)
                bit_conductor_id = query['bit_conductor'][0]
                bit_conductor = twitch_id_to_name_cached(bit_conductor_id)

                self.log_event("Hype Train End. Sub conductor %s, Bit conductor %s", sub_conductor, bit_conductor)
            elif type == 'progress':
                level = query['level'][0]
                progress = query['progress'][0]
                total = query['total'][0]
                self.log_event("Hype Train Progress: Level %s Progress %s Total %s", level, progress, total)
            elif type == 'conductor':
                sub_conductor_id = query['sub_conductor'][0]
                sub_conductor = twitch_id_to_name_cached(sub_conductor_id)
                bit_conductor_id = query['bit_conductor'][0]
                bit_conductor = twitch_id_to_name_cached(bit_conductor_id)

                self.log_event("Hype Train Conductor. Sub conductor %s, Bit conductor %s", sub_conductor, bit_conductor)
            elif type == 'cooldownover':
                self.log_event('Hype Train Cooldown Over')
            else:
                # Not a recognized type
                self.send_error(400)
                return
        else:
            # Non-hype train event
            adjust = 0
            points = 0
            points_set = False
            if 'bits' in query:
                name = query['name'][0]
                amount = query['bits'][0]
                points = int(config['event']['per100bits'] * int(amount) / 100)
                message = query['message'][0]
                self.log_event('\'' + name + '\' cheered ' + amount + ' bits (' + str(points) + ' points): ' + message)
            elif 'sub' in query:
                type = query['sub'][0]
                if type == 'self':
                    name = query['name'][0]
                    tier = query['tier'][0]
                    if tier == 'Prime':
                        points = int(config['event']['prime-sub'])
                    elif tier == 'Tier 1':
                        points = int(config['event']['t1-sub'])
                    elif tier == 'Tier 2':
                        points = int(config['event']['t2-sub'])
                    elif tier == 'Tier 3':
                        points = int(config['event']['t3-sub'])
                    else:
                        # Invalid tier
                        self.log_message('Have a self sub with a invalid tier')
                        self.send_error(400)
                        return
                    months = query['months'][0]
                    message = query['message'][0]

                    self.log_event('\'' + name + '\' subbed ' + tier + ' for ' + months + ' months (' + str(points) + ' points): ' + message)
                elif type == 'gift':
                    gifter = query['gifter'][0]
                    recipient = query['recipient'][0]
                    tier = query['tier'][0]
                    if tier == 'Tier 1':
                        points = int(config['event']['t1-sub'])
                    elif tier == 'Tier 2':
                        points = int(config['event']['t2-sub'])
                    elif tier == 'Tier 3':
                        points = int(config['event']['t3-sub'])
                    else:
                        # Invalid tier
                        self.log_message('Have a gift sub with a invalid tier')
                        self.send_error(400)
                        return
                    months = query['months'][0]

                    self.log_event('\'' + gifter + '\' gifted ' + tier + ' to \'' + recipient + '\' who now has ' + months + ' months (' + str(points) + ' points)')

                elif type == 'community':
                    name = query['name'][0]
                    quantity =  int(query['quantity'][0])
                    tier = query['tier'][0]
                    if tier == 'Tier 1':
                        points = int(config['event']['t1-sub']) * quantity
                    elif tier == 'Tier 2':
                        points = int(config['event']['t2-sub']) * quantity
                    elif tier == 'Tier 3':
                        points = int(config['event']['t3-sub']) * quantity
                    else:
                        # Invalid tier
                        self.log_message('Have a community gift sub with a invalid tier')
                        self.send_error(400)
                        return

                    self.log_event('\'' + name + '\' gifted ' + tier + ' to ' + str(quantity) + ' people (' + str(points) + ' points)')

                    pass
                else:
                    self.log_error('Have a sub with invalid type, skipping')
                    self.send_error(400)
                    return

            elif 'tip' in query:
                name = query['name'][0]
                amount = float(query['tip'][0])
                amount_after_fees = amount * (1.0 - config['event']['tip-fee-percent'] / 100) - config['event']['tip-fee-fixed']
                points = int(config['event']['perdollartip'] * amount_after_fees)
                message = query['message'][0]
                self.log_event('\'' + name + '\' tipped ' + str(amount) + ' (' + str(points) + ' points): ' + message)
            elif 'time' in query:
                direction = 0
                if query['time'][0] == 'increase':
                    direction = 1
                elif query['time'][0] == 'decrease':
                    direction = -1
                else:
                    #Invalid
                    self.log_message('Event time with invalid value')
                    self.send_response(400)
                    return
                if 'amount' not in query:
                    self.log_message('No amount specified')
                    self.send_response(400)
                    return

                today_no_time = datetime.datetime.combine(datetime.date.today(), datetime.time())
                amount = (parse(query['amount'][0]) - today_no_time).total_seconds()

                adjust = int(direction * amount)
                self.log_event('Adjust timer by ' + str(adjust) + ' seconds')

            elif 'points' in query:
                direction = 0
                if query['points'][0] == 'increase':
                    direction = 1
                elif query['points'][0] == 'decrease':
                    direction = -1
                elif query['points'][0] == 'set':
                    direction = 1
                    points_set = True
                else:
                    #Invalid
                    self.log_message('Event points with invalid value')
                    self.send_response(400)
                    return

                if 'amount' not in query:
                    self.log_message('Points even with no amount')
                    self.send_response(400)
                    return

                points = direction * int(query['amount'][0])
                if points_set:
                    self.log_event('Set timer to ' + str(points) + ' points')
                else:
                    self.log_event('Adjust timer by ' + str(points) + ' points')


            # Read in timer info
            timer_data = {}
            with open('timer_data.json') as f:
                timer_data = json.load(f)

            # Add to total
            if points_set:
                timer_data['points-funded'] = points
            else:
                timer_data['points-funded'] += points
            timer_data['time-adjust'] += adjust

            # Calculate stream end
            stream_start = datetime.datetime.fromisoformat(timer_data['stream-start'])
            stream_end = datetime.datetime.fromisoformat(timer_data['stream-end'])
            percent_funded = timer_data['points-funded'] / timer_data['points-to-fully-fund']
            time_adjust = datetime.timedelta(seconds=timer_data['time-adjust'])
            current_end = stream_start + percent_funded * config['timer']['time-fundable'] + time_adjust

            # Do not exceed stream end
            if current_end > stream_end:
                current_end = stream_end

            # Convert back to ISO Format and write out
            timer_data['current-end'] = current_end.isoformat(timespec='milliseconds')

            with open('timer_data.json', 'w') as f:
                json.dump(timer_data, f, indent=4)
        
        self.success_response()

    def handle_keypress(self):
        from pynput.keyboard import Key
        # Extract query
        query = parse_qs(urlparse(self.path).query)

        modifiers_map = {
            'alt': Key.alt, 'alt_gr': Key.alt_gr, 'alt_l': Key.alt_l, 'alt_r': Key.alt_r, 'ctrl': Key.ctrl,
            'ctrl_l': Key.ctrl_l, 'ctrl_r': Key.ctrl_r, 'shift': Key.shift, 'shift_l': Key.shift_l,
            'shift_r': Key.shift_r, 'super': Key.cmd
        }
        key_map = {
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4, 'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7,
            'f8': Key.f8, 'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12, 'f13': Key.f13,
            'f14': Key.f14, 'f15': Key.f15, 'f16': Key.f16, 'f17': Key.f17, 'f18': Key.f18, 'f19': Key.f19,
            'f20': Key.f20
        }

        # Determine key to press
        modifiers = []
        if 'mod' in query:
            modifiers = [modifiers_map[x] for x in query['mod']]

        if 'key' not in query:
            self.log_message("Requested keypress with no key")
            self.send_error(400)
            return

        keystring = query['key'][0]
        key = ''
        if keystring in 'abcdefghijklmnopqrstuvwxyz0123456789':
            key = keystring
        elif keystring in key_map:
            key = key_map[keystring]
        else:
            self.log_message("Unknown key: %s", keystring)
            self.send_error(400)
            return

        repeat = 1
        if 'repeat' in query:
            repeat = int(query['repeat'][0])

        delay = 0
        if 'delay' in query and repeat != 1:
            delay = int(query['delay'][0]) / 1000

        self.log_message("Pressing key %s with modifiers %s and repeat of %i and delay %i", key, modifiers, repeat, delay)

        x = threading.Thread(target=keypressWorker, args=(modifiers, key, repeat, delay))
        x.start()

        self.success_response()

    def handle_write(self):
        # Extract query
        query = parse_qs(urlparse(self.path).query)

        # Require both filename and data
        if not 'filename' in query:
            self.log_message("Missing query parameter filename")
            self.send_error(404)
            return
        if not 'data' in query:
            self.log_message("Missing query parameter data")
            self.send_error(404)
            return

        # Optional mode
        mode = 'w'
        if 'mode' in query:
            if query['mode'][0] == 'a':
                mode = 'a'
            elif query['mode'][0] != 'w':
                self.log_message("Unknown mode parameter '" + query['mode'][0] + "'")
                self.send_error(404)
                return

        filename = query['filename'][0]
        data = query['data'][0]

        # Optional timestamp and per line
        if 'log' in query:
            data = datetime.datetime.now().isoformat() + ' - ' + data + '\n'

        # Actually write to the file
        with open(filename, mode) as w:
            w.write(data)

        if mode == 'w':
            self.log_message("'" + filename + "' was overwritten with '" + data + "'")
        elif mode == 'a':
            self.log_message("'" + filename + "' was appended with '" + data + "'")

        self.success_response()

def keypressWorker(modifiers, key, repeat, delay):
    keyboard = pynput.keyboard.Controller()

    for i in range(repeat):
        # Press modifiers
        for m in modifiers:
            keyboard.press(m)

        # Press key
        keyboard.tap(key)

        # Release modifiers
        for m in modifiers:
            keyboard.release(m)

        time.sleep(delay)
        

def readConfig(filename):
    with open(filename) as f:
        config = json.load(f)

        # Convert inputs into datetime and timedeltas as appropriate
        
        config['timer']['stream-start'] = parse(config['timer']['stream-start'])

        # dateutil.parser will assume today's date if given something like "30s", subtract
        # off today's date to get a correct duration
        today_no_time = datetime.datetime.combine(datetime.date.today(), datetime.time())
        config['timer']['timer-start'] = parse(config['timer']['timer-start']) - today_no_time
        config['timer']['time-fundable'] = parse(config['timer']['time-fundable']) - today_no_time

        return config

def ensureTimerSetup(config):
    import os.path
    if os.path.exists('timer_data.json'):
        with open('timer_data.json') as f:
            timer_data = json.load(f)

            # Convert into datetimes
            timer_data['stream-start'] = parse(timer_data['stream-start'])
            timer_data['stream-end'] = parse(timer_data['stream-end'])
            timer_data['current-end'] = parse(timer_data['current-end'])

            now = datetime.datetime.now()
            if now <  timer_data['current-end']:
                print("Since current time is before end in timer_data.json, assuming script restarted during stream")
                return

    # No existing timer data or expired
    timer_data = {}
    timer_data['stream-start'] = config['timer']['stream-start'].isoformat()
    timer_data['stream-end'] = (config['timer']['stream-start'] + config['timer']['timer-start'] + config['timer']['time-fundable']).isoformat()
    timer_data['current-end'] = (config['timer']['stream-start'] + config['timer']['timer-start']).isoformat()
    timer_data['points-funded'] = 0
    timer_data['points-to-fully-fund'] = config['timer']['points-to-fully-fund']
    timer_data['time-adjust'] = 0

    with open('timer_data.json', 'w') as f:
        json.dump(timer_data, f, indent=4)

twitch_id_cache = {}
def twitch_id_to_name_cached(id):
    global twitch_id_cache

    # Check if already cached
    if id in twitch_id_cache:
        return twitch_id_cache[id]
    
    import requests
    r = requests.get('https://customapi.aidenwallis.co.uk/api/v1/twitch/toName/' + id)

    twitch_id_cache[id] = r.text

    return r.text

def version_string():
    return "0.0.5"

def setup_logging():
    import logging.handlers

    # Ensure there is a logs directory
    import os
    os.makedirs('logs', exist_ok=True)

    # Setup a rotating debug log
    debug_handler = logging.handlers.TimedRotatingFileHandler(
        filename='logs/debug.log',
        when='d',
        interval=1,
        backupCount=10
    )
    debug_formatter = logging.Formatter('%(asctime)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s')
    debug_handler.setFormatter(debug_formatter)
    debug_handler.setLevel(logging.DEBUG)

    # Setup rotating event log
    event_handler = logging.handlers.TimedRotatingFileHandler(
        filename='logs/events.log',
        when='d',
        interval=1,
    )
    event_formatter = logging.Formatter('%(asctime)s - %(message)s')
    event_handler.setFormatter(event_formatter)
    event_handler.setLevel(logging.INFO)

    # Attach handlers
    global logger
    logger = logging.getLogger('root')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(debug_handler)
    logger.addHandler(event_handler)


def startServer():
    setup_logging()
    global config
    config = readConfig('config.json')
    ensureTimerSetup(config)
 
    print("WritingHTTPServer " + version_string() + " by Number6174")
    print("Server started on http://" + config['host'] + ":" + str(config['port']))
    print("Use CTRL+C to stop")

    # Setup server
    handler = WritingHttpRequestHandler
    server = http.server.HTTPServer((config['host'], config['port']), handler)

    # Start the server
    server.serve_forever()


if __name__ == "__main__":
    startServer()