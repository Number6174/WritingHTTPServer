# WritingHTTPServer
A simple Python HTTP server that writes GET parameters to a specified file.
It also supports a timer that can be extended by specific events.

WARNING: This is a very purpose driven program. If you don't completely understand how to use it, it could
expose you to security vulnerabilities. Do not open this program to the broader internet. Only allow it to
accept local connections. It uses Python's [http.server](https://docs.python.org/3/library/http.server.html)
which is not hardened. In addition, the CORS header `Access-Control-Allow-Origin` is set to `*` for some end
points which bypasses the security that CORS can help provide.

The provided configuration has it listen only on 127.0.0.1. It is not recommended that you change this.

# Setup

1. Install Python for [Windows](https://www.python.org/downloads/windows/) (tested with 3.9.3)
2. Verify Python is in your PATH. This can be done by running
`python --version` in the Windows Terminal. You should see a response like `Python 3.9.3`
3. Ensure the following Python packages are installed. You may wish to do this in a [venv](https://docs.python.org/3/tutorial/venv.html). Each can be installed as `pip install`
    * python-dateutil

# Configuration

## Web interface

When the script is running, on say port 8001, accessing [http://127.0.0.1:8001](http://127.0.0.1:8001) will provide
a web interface to many of the options of the script.

## `config.json`

Edit the included `config.json`. The program must be restarted to load any configuration changes

* `host` - This defines the host to listen to. It is strongly recommended to only be 127.0.0.1
* `port` - The port to listen on. The default configuration uses 8001.

All the dates and times go through [dateutils's parser](https://dateutil.readthedocs.io/en/stable/parser.html)
which is very generous on formatting. Valid formats include: "5pm", "17:00", "2021-03-14-05", "March 14 at 5pm",
"3 hours", "3h", "1 minute", "1m", "30 seconds", "30s", "1m30s", among others.

Under `event`, you'll find:

* `per100bits` - How many points per 100 bits cheered, e.g. `100`
* `perdollartip` - How many points per 1 dollar in tips, e.g. `100`
* `prime-sub` - How many points per Prime sub, e.g. `250`
* `t1-sub` - How many points per Tier 1 sub, e.g. `250`
* `t2-sub` - How many points per Tier 2 sub, e.g. `500`
* `t3-sub` - How many points per Tier 3 sub, e.g. `1250`

Under `timer`, you'll find:

* `stream-start` - When your stream normally starts, e.g. `5pm`
* `timer-start` - How much to start the timer with prior to any bits/subs/tips, e.g. `3h`
* `time-fundable` - How long the timer can be extended, e.g. `9h`
* `points-to-fully-fund` - How many points from events need to occur to fully fund

# Use

Open up a terminal. Navigate to the directory where `server.py` exists.
Type `python server.py`

It will start a webserver on port 8001. The port is configurable only by editing the script.

To stop the program, hit CTRL+C.

## /api
This provides REST style information. These are here to simplify using some of the information managed by this script.
It permits an HTML file to not care where a file is present on a hard drive and need only know the URL to obtain the
data.

### /api/timer
Returns the contents of `timer_data.json`. 

### /api/config
Returns the contents of `config.json`.

## /event

This endpoint records various events. It is recommended you call this endpoint for each bit, sub, and tip.

Each event should have both a name and event type. The name is specified by either `name` or `twitch_id`.
The event type can be one of `bits`, `sub`, or `tip`.

    http://127.0.0.1:8001/event?name=Username&bits=amount
    http://127.0.0.1:8001/event?name=Username&sub=amount&tier=tier
    http://127.0.0.1:8001/event?name=Username&tip=amount

Amount must be an integer, typically the value of `1` except for community gift subs. Tier must be one of "Prime", "Tier 1", "Tier 2", or "Tier 3".

If you wish to use Hype Train information, use the following

    http://127.0.0.1:8001/event?train=start
    http://127.0.0.1:8001/event?train=end&sub_conductor=id&bit_conductor=id
    http://127.0.0.1:8001/event?train=progress&level=level&progress=amount&total=amount
    http://127.0.0.1:8001/event?train=conductor&bit_conductor=id&bit_conductor=id
    http://127.0.0.1:8001/event?train=cooldownover

If you are using Kruiz Control, this should correspond to the data you obtain from the events `OnHypeTrainStart`,
`OnHypeTrainEnd`, `OnHypeTrainProgress`, `OnHypeTrainConductor`, and `OnHypeTrainCooldownExpired`, respectively.

To arbitrarily shift the timer or points

    http://127.0.01:8001/event?time=increase&amount=howmuch
    http://127.0.01:8001/event?time=decrease&amount=howmuch
    http://127.0.01:8001/event?points=increase&amount=howmuch
    http://127.0.01:8001/event?points=decrease&amount=howmuch
    http://127.0.01:8001/event?points=set&amount=howmuch

Where `howmuch` is either a string to go through dateutil's parser for the time amounts, or an integer for the points.

Each version of this endpoint will appropriately adjust the timer.

## /write

For URLs of the form:

    http://127.0.0.1:8001/write?filename=filename.txt&data=contents

It will open up the filename `filename.txt` and replace the contents with `contents`.
Unless otherwise specified, the file `filename.txt` will be in the same directory as the script.
Be careful of what file you specify, if it is important, it will be overwritten.

There are optional query parameters of `mode`, and `log`. The `mode` parameter accepts either `w` to overwrite the file contents or `a` to append to the file. The `log` paramater ignores any values, but if present, will put the new data on a line by itself with a timestamp.

For example, if you made the two successive requests of

    http://127.0.0.1:8001/write?filename=filename.txt&mode=a&data=1
    http://127.0.0.1:8001/write?filename=filename.txt&mode=a&data=2

It would result in the file `filename.txt` containing:

    12

But if you had the two successive requests of

    http://127.0.0.1:8001/write?filename=filename.txt&mode=a&log=true&data=1
    http://127.0.0.1:8001/write?filename=filename.txt&mode=a&log=true&data=2

It would result in the file `filename.txt` containing something like:

    2021-04-08T09:37:20.769127 - 1
    2021-04-08T09:37:21.799855 - 2
