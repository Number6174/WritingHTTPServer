# WritingHTTPServer
A simple Python HTTP server that writes GET parameters to a specified file

WARNING: This is a very purpose driven program. If you don't completely understand how to use it, it could expose you to security vulnerabilities. Do not open this program to the broader internet. Only allow it to accept local connections.

By default it only listens on 127.0.0.1

# Setup
1. Install Python for [Windows](https://www.python.org/downloads/windows/) (tested with 3.9.2)
2. Verify Python is in your PATH. This can be done by running
`python --version` in the Windows Terminal. You should see a response like `Python 3.9.2`

# Use
Open up a terminal.
Type `python server.py`

It will start a webserver on port 8001, configurable only by editing the script.

To stop the program, hit CTRL+C.

The server will respond to URLs of the form:
    http://127.0.0.1:8001/write?filename=filename.txt&data=contents

It will open up the filename `filename.txt` and replace the contents with `contents`.
Unless otherwise specified, the file `filename.txt` will be in the same directory as the script.