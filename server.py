import http.server
from urllib.parse import urlparse
from urllib.parse import parse_qs
import datetime
import json
from dateutil.parser import parse

class WritingHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Handle the request
        url = urlparse(self.path)
        if url.path == '/':
            self.path = 'control_panel.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif url.path.startswith('/api'):
            self.handle_api()
        elif url.path == '/event':
            self.handle_event()
        elif url.path == '/write':
            self.handle_write()
        elif url.path == '/timer':
            self.handle_timer()
        else:
            self.log_message("Ignoring request to " + self.path)
            self.send_error(404)

    def success_response(self):
        # Write response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"<html><head></head><body>Success</body></html>"
        self.wfile.write(bytes(html, "utf8"))

    def handle_api(self):
        url = urlparse(self.path)
        if url.path == '/api/timer':
            # Open timer_data.json
            with open('timer_data.json') as f:
                data = json.load(f)
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
        self.log_message('Unknown API call ' + url.path)
        self.send_error(400)

    def handle_event(self):
        # Extract query
        query = parse_qs(urlparse(self.path).query)

        global config

        if 'train' in query:
            # Some kind of hype train event
            pass
        else:
            # Non-hype train event
            name = ""
            if 'name' in query:
                name = query['name'][0]
            
            points = 0
            if 'bits' in query:
                amount = query['bits'][0]
                points = config['event']['per100bits'] * int(amount) / 100
                self.log_message('User: \'' + name + '\' cheered ' + amount + ' bits which is ' + str(points) + ' points')
            elif 'sub' in query:
                amount = int(query['sub'][0])
                if not 'tier' in query:
                    # Have a sub without a tier, that is an error
                    self.log_message('Have a sub without a tier, skipping')
                    self.send_error(400)
                    return
                tier = query['tier'][0]
                if tier == 'Prime':
                    points = int(config['event']['prime-sub']) * amount
                elif tier == 'Tier 1':
                    points = int(config['event']['t1-sub']) * amount
                elif tier == 'Tier 2':
                    points = int(config['event']['t2-sub']) * amount
                elif tier == 'Tier 3':
                    points = int(config['event']['t3-sub']) * amount
                else:
                    # Invalid tier
                    self.log_message('Have a sub with a invalid tier')
                    self.send_error(400)
                    return


            # Read in timer info
            timer_data = {}
            with open('timer_data.json') as f:
                timer_data = json.load(f)

            # Add to total
            timer_data['points-funded'] += points

            # Calculate stream end
            stream_start = datetime.datetime.fromisoformat(timer_data['stream-start'])
            stream_end = datetime.datetime.fromisoformat(timer_data['stream-end'])
            current_end = stream_start + (timer_data['points-funded'] / timer_data['points-to-fully-fund']) * config['timer']['time-fundable']

            # Do not exceed stream end
            if current_end > stream_end:
                current_end = stream_end

            # Convert back to ISO Format and write out
            timer_data['current-end'] = current_end.isoformat()

            with open('timer_data.json', 'w') as f:
                json.dump(timer_data, f, indent=4)
        
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
            from datetime import datetime
            data = datetime.now().isoformat() + ' - ' + data + '\n'

        # Actually write to the file
        with open(filename, mode) as w:
            w.write(data)

        if mode == 'w':
            self.log_message("'" + filename + "' was overwritten with '" + data + "'")
        elif mode == 'a':
            self.log_message("'" + filename + "' was appended with '" + data + "'")

        self.success_response()

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

    with open('timer_data.json', 'w') as f:
        json.dump(timer_data, f, indent=4)


def startServer():
    global config
    config = readConfig('config.json')
    ensureTimerSetup(config)
 
    print("Server started on http://" + config['host'] + ":" + str(config['port']))
    print("Use CTRL+C to stop")

    # Setup server
    handler = WritingHttpRequestHandler
    server = http.server.HTTPServer((config['host'], config['port']), handler)

    # Start the server
    server.serve_forever()


if __name__ == "__main__":
    startServer()