<!--
SPDX-FileCopyrightText: 2021 Number6174
SPDX-License-Identifier: CC0-1.0
-->

# WritingHTTPServer
A simple Python HTTP server that writes to files, simulates keypresses, records events, manages a timer,
and manages information about a hype train. It is intended to be used with [Kruiz Control](https://github.com/Kruiser8/Kruiz-Control/tree/master).

**WARNING**: This is a very purpose driven program. If you don't completely understand how to use it, it could
expose you to security vulnerabilities. Do not open this program to the broader internet. Only allow it to
accept local connections. It uses Python's [http.server](https://docs.python.org/3/library/http.server.html)
which is not hardened. In addition, the CORS header `Access-Control-Allow-Origin` is set to `*` for some end
points which bypasses the security that CORS can help provide.

The provided configuration has it listen only on 127.0.0.1. It is not recommended that you change this.

[![REUSE status](https://api.reuse.software/badge/github.com/Number6174/WritingHTTPServer)](https://api.reuse.software/info/github.com/Number6174/WritingHTTPServer)


# Setup

## Using a release version
1. Download the zip file from the [latest release](https://github.com/Number6174/WritingHTTPServer/releases/latest)
2. Unzip in a directory where the script will have write permissions

## Manual
1. Install Python for [Windows](https://www.python.org/downloads/windows/) (tested with 3.12.5)
2. Verify Python is in your PATH. This can be done by running
`python --version` in the Windows Terminal. You should see a response like `Python 3.12.5`
3. Verify [Poetry](https://python-poetry.org/) is set up and working
4. Run `poetry install` to install the dependencies

# Use

## Using a release version
1. Unzip the downloaded zip into a location where the program will have write permissions.
2. Run `server.exe`.

To stop the program, just close the terminal window.

## Manual
Open up a terminal. Navigate to the directory where `server.py` exists.
Type `python server.py`

To stop the program, hit CTRL+C.

# Configuration

## Web interface

When the script is running, on say port 8001, accessing [http://127.0.0.1:8001](http://127.0.0.1:8001) will
provide a web interface to many of the options of the script. Everything can be edited here except the
`host` and `port`.

## config.json

Edit the included `config.json`. The program must be restarted to load any configuration changes

* `host` - This defines the host to listen to. It is strongly recommended to only be 127.0.0.1
* `port` - The port to listen on. The default configuration uses 8001.

All the dates and times go through [dateutils's parser](https://dateutil.readthedocs.io/en/stable/parser.html)
which is very generous on formatting. Valid formats include: "5pm", "17:00", "2021-03-14-05", "March 14 at 5pm",
"3 hours", "3h", "1 minute", "1m", "30 seconds", "30s", "1m30s", among others.

Under `event`, you'll find:

* `per100bits` - How many points per 100 bits cheered, e.g. `100`
* `perdollartip` - How many points per 1 dollar in tips, e.g. `100`
* `tip-fee-percent` - What percent of a tip is paid as a fee, e.g. `2.9`
* `tip-fee-fixed` - What fixed cost of a tip is paid as a fee, e.g. `0.3`
* `perdollarhypechat` - How many points per dollar of Hype Chat, e.g. `100`
* `hype-chat-currency` - Currency to convert Hype Chats too, e.g. `usd`. Make sure to use the [ISO 4217 currency code](https://en.wikipedia.org/wiki/ISO_4217#List_of_ISO_4217_currency_codes) in lower case.
* `hype-chat-fee-percent` - What percent of a Hype Chat paid as a fee, e.g. `33.5`
* `prime-sub` - How many points per Prime sub, e.g. `250`
* `t1-sub` - How many points per Tier 1 sub, e.g. `250`
* `t2-sub` - How many points per Tier 2 sub, e.g. `500`
* `t3-sub` - How many points per Tier 3 sub, e.g. `1250`

Under `timer`, you'll find:

* `stream-start` - When your stream normally starts, e.g. `5pm`
* `timer-start` - How much to start the timer with prior to any bits/subs/tips, e.g. `3h`
* `time-fundable` - How long the timer can be extended, e.g. `9h`
* `points-to-fully-fund` - How many points from events need to occur to fully fund

Under `rewasd`, you'll find:

* `path` - Where to find the reWASDCommandLine exectuable, e.g. `C:/Program Files/reWASD/reWASDCommandLine.exe` 

# Endpoints
This program provides several endpoint accessible over HTTP. The endpoints that are documented here are the only
ones you should rely upon.

## /api
This provides REST style information. These are here to simplify using some of the information managed by this
script. It permits an HTML file to not care where a file is present on a hard drive and need only know the URL
to obtain the data.

### GET /api/currency
For URLs of the form:

    http://127.0.0.1:8001/api/currency?amount=X&exponent=Y&currency=Z

Where
* `amount` is the amount to convert
* `exponent` if present, how many decimal points to shift amount by
* `currency` is an [ISO 4217 currency code](https://en.wikipedia.org/wiki/ISO_4217#List_of_ISO_4217_currency_codes)

Performs a currency conversion using [this API](https://github.com/fawazahmed0/currency-api).
Returns just a string of the converted amount

### GET /api/rewasd_queue
Returns a JSON representation of the current events in the reWASD queue.

### GET /api/timer
Returns the contents of `timer_data.json`. This is the best way to obtain the current timer information.
See [examples/timer.html](examples/timer.html) for how you might use this.

### GET /api/resettimer
Resets the contents of `timer_data.json` as if it were a non-existing file, or the program was restarted with that
file containing stale data.

## GET /event

This endpoint records various events. It is recommended you call this endpoint for each bit, sub, and tip.

### Bits
    http://127.0.0.1:8001/event?name=username&bits=amount&message=msg

Where
* `username` should be the display name of the cheerer
* `amount` is an integer
* `msg` is a string of the message.

If you are using Kruiz Control, this would be triggered by one of `OnSETwitchBits`, `OnSLTwitchBits`, or `OnSLTwitchBitsNoSync`.

### Subs
    http://127.0.0.1:8001/event?sub=self&name=username&tier=t&months=amount&message=msg

Where
* `username` should be the display name of the sub
* `t` is the tier and must be one of "Prime", "Tier 1", "Tier 2", "Tier 3", "1000", "2000", or "3000".
  If it is not one of these, it is treated as "Tier 1".
* `amount` is an integer
* `msg` is a string along the message.

If you are using Kruiz Control, this would be triggered by `OnSETwitchSub`, `OnSLTwitchSub`, or `OnSLTwitchSubNoSync`.

### Gift Subs
    http://127.0.0.1:8001/event?sub=gift&gifter=username1&recipient=username2&tier=t&months=amount

Where
* `username1` should be the display name of the gifter
* `username2` should be the display name of the recipient
* `t` is the tier and must be one of "Tier 1", "Tier 2", "Tier 3", "1000", "2000", "3000".
  If it is not one of these, it is treated as "Tier 1".
* `amount` is an integer

If you are using Kruiz Control, this would be triggered by `OnSETwitchGiftSub`, `OnSLTwitchGiftSub` `OnSLTwitchGiftSubNoSync`.

### Community Gift Subs
    http://127.0.0.1:8001/event?sub=community&name=username&quantity=amount&tier=t

Where
* `username` should be the display name of the gifter
* `amount` is an integer
* `t` is the tier and must be one of "Tier 1", "Tier 2", "Tier 3", "1000", "2000", "3000".
  If it is not one of these, it is treated as "Tier 1".

If you are using Kruiz Control, this would be triggered by `OnSETwitchBulkGiftSub`, `OnSLTwitchCommunityGiftSub` `OnSLTwitchCommunityGiftSubNoSync`


### Tips
    http://127.0.0.1:8001/event?name=username&tip=amount&message=msg

Where
* `username` should be the display name of the tipper
* `amount` is a number, including floats
* `msg` is a string of the message.

If you are using Kruiz Control, this would be triggered by `OnSEDonation`, `OnSLDonation`, `OnSLDonationNoSync`, `OnSLTiltifyDonation`, `OnSLTiltifyDonationNoSync`, or similar

### Hype Chat
    http://127.0.0.1:8001/event?name=username&hype_chat=amount&currency=currency_code&exponent=exp&message=msg

Where
* `username` should be the display name of the Hype Chatter
* `amount` is a number
* `currency_code` is an [ISO 4217 currency code](https://en.wikipedia.org/wiki/ISO_4217#List_of_ISO_4217_currency_codes)
* `exp` indicates how many decimal points this currency represents partial amounts in. For example, USD uses 2
* `msg` is a string of the message

Currency conversion uses [this API](https://github.com/fawazahmed0/currency-api). The current day's rates are cached upon script startup.

Right now Twitch does not provide a nice API for Hype Chats. So if you are using Kruiz Control, you can use this workaround:

```
OnEveryChatMessage
Function 'var d = [data]; return {is_hype_chat: "pinned-chat-paid-amount" in d.extra.userState}'
if 1 {is_hype_chat} = false
exit
Function 'var d = [data]; return {hc_amount: d.extra.userState["pinned-chat-paid-amount"], hc_currency: d.extra.userState["pinned-chat-paid-currency"], hc_exponent: d.extra.userState["pinned-chat-paid-exponent"]}'
API GET http://127.0.0.1:8001/event?name={user}&hype_chat={hc_amount}&currency={hc_currency}&exponent={hc_exponent}&message={message}
```

### Hype train
If you wish to use Hype Train information, use the following

    http://127.0.0.1:8001/event?train=start
    http://127.0.0.1:8001/event?train=end&sub_conductor=id&bit_conductor=id
    http://127.0.0.1:8001/event?train=progress&level=level&progress=amount&total=amount
    http://127.0.0.1:8001/event?train=conductor&bit_conductor=id&bit_conductor=id
    http://127.0.0.1:8001/event?train=cooldownover

If you are using Kruiz Control, this should correspond to the data you obtain from the events `OnHypeTrainStart`,
`OnHypeTrainEnd`, `OnHypeTrainProgress`, `OnHypeTrainConductor`, and `OnHypeTrainCooldownExpired`, respectively.

### Shifting timer
To arbitrarily shift the timer or points

    http://127.0.01:8001/event?time=increase&amount=howmuch
    http://127.0.01:8001/event?time=decrease&amount=howmuch
    http://127.0.01:8001/event?points=increase&amount=howmuch
    http://127.0.01:8001/event?points=decrease&amount=howmuch
    http://127.0.01:8001/event?points=set&amount=howmuch

Where `howmuch` is either a string to go through dateutil's parser for the time amounts, or an integer for the points.

Each version of this endpoint will appropriately adjust the timer.

## GET /keypress

This endpoint simulates keypresses. This uses [pynput](https://pynput.readthedocs.io/en/latest/index.html), so
that does mean there are some [limitations](https://pynput.readthedocs.io/en/latest/limitations.html#windows).


The keys supported are a-z, 0-9, f1-f20 with modifiers alt, alt_gr, alt_l, alt_r, ctrl, ctrl_l, ctrl_r, 
shift, shift_l, shift_r, and super.

Select one key and as many modifiers as you like. For example

    http://127.0.0.1:8001/keypress?key=a&mod=alt&mod=shift&mod=ctrl

Presses `Ctrl+Alt+Shift-a`.

    http://127.0.0.1:8001/keypress?key=f14

Presses `F14`.

    http://127.0.0.1:8001/keypress?key=a&repeat=4

Presses `a` four times.

    http://127.0.0.1:8001/keypress?key=f13&mod=ctrl&repeat=4&delay=500

Presses `f13` four times with a delay of 0.5 seconds between each press.

### AutoHotkey
Depending on your usage you may need to combine with [AutoHotKey](https://www.autohotkey.com/) to send keypresses
to specific windows, such as:

    ^F13::
    SetKeyDelay, 50,100 ; This helps with reliability.
    ControlSend,, b, Window Title
    return

This example takes `Ctrl-F13` and sends the key `b` to an application with the window title `Window Title`.

This kind of workaround is often useful to send a specific keystroke to a program that is not the active program.

## GET /rewasd

This endpoint interacts with the program [reWASD](https://www.rewasd.com/) using their [command line interface](https://help.rewasd.com/interface/command-line.html).

Each of the variations will require a device-id. From reWASD's documentation:
> To find it, please choose the device or the group you are working with in reWASD GUI, right-click to open the
> context menu and choose Copy device ID option.

You might need some of reWASD's "Advanced Features" which requires more than a basic license. The program will print
an error message if you don't have the correct license.

### Apply a config

For URLs of the form:

    http://127.0.0.1:8001/rewasd?device_id=XYZ&apply=path&slot=slotX

Where
* `device_id` is the device id to modify
* `apply` is the path of the config to apply, including extension. To find where your config is stored, right-click a
   certain config and choose Open file location option; then copy the path, and add the name of the config file to it,
   along with the file extension
* `slot` is the slot to apply it too. Must be one of `slot1`, `slot2`, `slot3`, `slot4`.

### Activate a slot

For URLs of the form:

    http://127.0.0.1:8001/rewasd?device_id=XYZ&name=Foo&duration=number&change_to=slotX&return_to=slotY

Where
* `device_id` is the device id to modify
* `name` is the queue to add time too 
* `duration` is the number of seconds to apply the swap
* `change_to` is the slot to change the device too. Must be one of `slot1`, `slot2`, `slot3`, `slot4`.
* `return_to` is the slot to change to after the duration has elapsed

This will change the `device_id` to the `change_to` slot and when complete, change it to the `return_to` slot.

This internally uses a timer system so only one change is active at any moment. The events will queue up. The "same"
event will coalesce together. Two events are considered the same if they have the same `name`.

## GET /write

For URLs of the form:

    http://127.0.0.1:8001/write?filename=filename.txt&data=contents

It will open up the filename `filename.txt` and replace the contents with `contents`.
Unless otherwise specified, the file `filename.txt` will be in the same directory as the script.
Be careful of what file you specify, if it is important, it will be overwritten.

There are optional query parameters of `mode`, `prepend_newline`, `append_newline` and `log`.
* The `mode` parameter accepts either `w` to overwrite the file contents or `a` to append to the file.
* The `prepend_newline` parameter ignores any values, but if present, will put a newline prior to the new data.
* The `append_newline` parameter ignores any values, but if present, will put a newline after the new data. 
* The `log` parameter ignores any values, but if present, will put the new data on a line by itself with a timestamp.

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

# Development Notes
If you intend to build an exe using pyinstaller, you must first install `pyinstaller` via pip, then run:

    pyinstaller server.spec

For support file Github issues or join the [Discord](https://discord.gg/MpN36Fnpf2).

The code is formatted with [Black](https://black.readthedocs.io/) and linted with [ruff](https://github.com/astral-sh/ruff).
