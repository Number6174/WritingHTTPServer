import http.server
from urllib.parse import urlparse
from urllib.parse import parse_qs

class WritingHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Only answer calls to /write
        url = urlparse(self.path)
        if url.path != '/write':
            self.log_message("Ignoring request to " + self.path)
            self.send_error(404)

        # Extract query
        query = parse_qs(url.query)

        # Require both filename and data
        if not 'filename' in query:
            self.log_message("Missing query parameter filename")
            self.send_error(404)
        if not 'data' in query:
            self.log_message("Missing query parameter data")
            self.send_error(404)

        filename = query['filename'][0]
        data = query['data'][0]

        # Actually write to the file
        with open(filename, 'w') as w:
            w.write(data)

        self.log_message("To the filename '" + filename + "', the contents '" + data + "' was written")

        # Write response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"<html><head></head><body>Success</body></html>"
        self.wfile.write(bytes(html, "utf8"))

        return


def startServer():
    HOST = '127.0.0.1'
    PORT = 8001

    print("Server started on http://" + HOST + ":" + str(PORT))
    print("Use CTRL+C to stop")

    # Setup server
    handler = WritingHttpRequestHandler
    server = http.server.HTTPServer((HOST, PORT), handler)

    # Start the server
    server.serve_forever()

if __name__ == "__main__":
    startServer()