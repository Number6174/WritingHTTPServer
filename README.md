# WritingHTTPServer
A simple Python HTTP server that writes GET parameters to a specified file.
It also supports a timer that can be extended by specific events.

WARNING: This is a very purpose driven program. If you don't completely understand how to use it, it could expose you to security vulnerabilities. Do not open this program to the broader internet. Only allow it to accept local connections.

The provided configuration has it listen only on 127.0.0.1. It is not recommended that you change this.

# Setup

1. Install Python for [Windows](https://www.python.org/downloads/windows/) (tested with 3.9.2)
2. Verify Python is in your PATH. This can be done by running
`python --version` in the Windows Terminal. You should see a response like `Python 3.9.2`
3. Install dateutil. This is easiest to do by typing `pip install python-dateutil` at the command line.

# Configuration

Edit the included `config.json`. The program must be restarted to load any configuration changes

* "host" - This defines the host to listen to. It is strongly recommended to only be 127.0.0.1
* "port" - The port to listen on. The default configuration uses 8001.

All the dates and times go through [dateutils's parser](https://dateutil.readthedocs.io/en/stable/parser.html)
which is very generous on formatting. Valid formats include: "5pm", "17:00", "2021-03-14-05", "March 14 at 5pm",
"3 hours", "3h", "1 minute", "1m", "30 seconds", "30s", "1m30s", among others.

Under timer, you'll find:

* "stream-start" - When your stream normally starts, e.g. "5pm"
* "stream-end" - The maximum time your stream can end, e.g. "5am"
* "timer-start" - How much to start the timer with prior to any bits/subs/tips, e.g. "3h"
* "prime-sub" - How much time should be added for a Twitch Prime Sub, e.g. "30s"
* "t1-sub" - How much time should be added for a Tier 1 Twitch Sub, e.g. "30s"
* "t2-sub" - How much time should be added for a Tier 2 Twitch Sub, e.g. "1m"
* "t3-sub" - How much time should be added for a Tier 2 Twitch Sub, e.g. "2m30s"
* "per100bits" - How much time should be added for every 100 bits on Twitch, e.g. "6s"
* "perdollartip" - How much time should be added for dollar of a tip, e.g."6s"

# Use

Open up a terminal. Navigate to the directory where `server.py` exists.
Type `python server.py`

It will start a webserver on port 8001. The port is configurable only by editing the script.

To stop the program, hit CTRL+C.

## /timer

This modifies the file `timer_data.json` which is intended to be paired with timer.html

For URLs of the form:

    http://127.0.0.1:8001/timer?bits=amount
    http://127.0.0.1:8001/timer?sub=amount&tier=tier
    http://127.0.0.1:8001/timer?tip=amount

It will increase the end time by an appropriate amount according to the config values.
In the case of a gift sub or resub, use the amount of 1. The amount is primarily there for community gift subs.
The acceptable values for tier are "Prime", "Tier 1", "Tier 2", or "Tier 3"

## /write

For URLs of the form:

    http://127.0.0.1:8001/write?filename=filename.txt&data=contents

It will open up the filename `filename.txt` and replace the contents with `contents`.
Unless otherwise specified, the file `filename.txt` will be in the same directory as the script.
Be careful of what file you specify, if it is important, it will be overwritten.