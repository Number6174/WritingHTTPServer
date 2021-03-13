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
        if url.path == '/write':
            self.handle_write()
        elif url.path == '/timer':
            self.handle_timer()
        else:
            self.log_message("Ignoring request to " + self.path)
            self.send_error(404)

        # Write response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"<html><head></head><body>Success</body></html>"
        self.wfile.write(bytes(html, "utf8"))

        return

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

        filename = query['filename'][0]
        data = query['data'][0]

        # Actually write to the file
        with open(filename, 'w') as w:
            w.write(data)

        self.log_message("To the file named '" + filename + "', the contents '" + data + "' was written")

    def handle_timer(self):
        # Extract query
        query = parse_qs(urlparse(self.path).query)

        # Calculate how much should be added to the timer
        time_added = 0
        global config
        if 'bits' in query:
            time_added = config['timer']['per100bits'] * int(query['bits'][0]) / 100
            self.log_message(query['bits'][0] + ' bits adds up to ' + str(time_added) + ' to the timer')
        elif 'sub' in query and 'tier' in query:
            if query['tier'][0].lower() == 'prime':
                time_added = config['timer']['prime-sub'] * int(query['sub'][0])
                self.log_message(query['sub'][0] + ' prime sub adds up to ' + str(time_added) + ' to the timer')
            elif query['tier'][0].lower() == 'tier 1':
                time_added = config['timer']['t1-sub'] * int(query['sub'][0])
                self.log_message(query['sub'][0] + ' tier 1 subs adds up to ' + str(time_added) + ' to the timer')
            elif query['tier'][0].lower() == 'tier 2':
                time_added = config['timer']['t2-sub'] * int(query['sub'][0])
                self.log_message(query['sub'][0] + ' tier 2 subs adds up to ' + str(time_added) + ' to the timer')
            elif query['tier'][0].lower() == 'tier 3':
                time_added = config['timer']['t3-sub'] * int(query['sub'][0])
                self.log_message(query['sub'][0] + ' tier 3 subs adds up to ' + str(time_added) + ' to the timer')
            else:
                self.log_message("Unknown tier of " + query['tier'][0])
        elif 'tip' in query:
            time_added = config['timer']['perdollartip'] * float(query['tip'][0])
            self.log_message(query['tip'][0] + ' tip adds up to ' + str(time_added) + ' to the timer')
        else:
            self.log_message("Unknown query")
            return

        # Read in timer info

        timer_data = {}
        with open('timer_data.json') as f:
            timer_data = json.load(f)

        # Determine if change needed
        if timer_data['current-end'] == timer_data['stream-end']:
            # Already at max extension
            self.log_message("Already maxed out timer")
            return

        # Adding at least some time
        current_end = datetime.datetime.fromisoformat(timer_data['current-end'])
        stream_end = datetime.datetime.fromisoformat(timer_data['stream-end'])
        current_end += time_added

        # Do not exceed stream end
        if current_end > stream_end:
            current_end = stream_end

        # Convert back to ISO Format and write out
        timer_data['current-end'] = current_end.isoformat()

        with open('timer_data.json', 'w') as f:
            json.dump(timer_data, f, indent=4)



def readConfig(filename):
    with open(filename) as f:
        config = json.load(f)

        # Convert inputs into datetime and timedeltas as appropriate
        
        config['timer']['stream-start'] = parse(config['timer']['stream-start'])
        config['timer']['stream-end'] = parse(config['timer']['stream-end'])

        if config['timer']['stream-end'] < config['timer']['stream-start']:
            # Assume the stream crosses a midnight boundary
            config['timer']['stream-end'] += datetime.timedelta(days=1)

        # dateutil.parser will assume today's date if given something like "30s", subtract
        # off today's date to get a correct duration
        today_no_time = datetime.datetime.combine(datetime.date.today(), datetime.time())
        config['timer']['timer-start'] = parse(config['timer']['timer-start']) - today_no_time
        config['timer']['prime-sub'] = parse(config['timer']['prime-sub']) - today_no_time
        config['timer']['t1-sub'] = parse(config['timer']['t1-sub']) - today_no_time
        config['timer']['t2-sub'] = parse(config['timer']['t2-sub']) - today_no_time
        config['timer']['t3-sub'] = parse(config['timer']['t3-sub']) - today_no_time

        config['timer']['per100bits'] = parse(config['timer']['per100bits']) - today_no_time
        config['timer']['perdollartip'] = parse(config['timer']['perdollartip']) - today_no_time

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
            if timer_data['stream-start'] < now and now <  timer_data['current-end']:
                print("Since current time is between start and end in timer_data.json, assuming script restarted during stream")
                return

    # No existing timer data or expired
    timer_data = {}
    timer_data['stream-start'] = config['timer']['stream-start'].isoformat()
    timer_data['stream-end'] = config['timer']['stream-end'].isoformat()
    timer_data['current-end'] = (config['timer']['stream-start'] + config['timer']['timer-start']).isoformat()

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