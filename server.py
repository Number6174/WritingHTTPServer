# SPDX-FileCopyrightText: 2021 Number6174
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import datetime
import http.server
import json
from json import JSONEncoder
import logging
import logging.handlers
import os
import os.path
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qs
from urllib.parse import urlparse

import httpx
import pynput
from dateutil.parser import parse
from pynput.keyboard import Key


class WritingHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_error(self, format, *args):
        global logger
        logger.error(format % args)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global logger
        # Handle the request
        url = urlparse(self.path)
        if url.path == "/":
            self.path = "control_panel.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif url.path == "/favicon.ico":
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif url.path.startswith("/api"):
            self.handle_api()
        elif url.path == "/event":
            logger.debug("%s", url)
            self.handle_event()
        elif url.path == "/keypress":
            logger.debug("%s", url)
            self.handle_keypress()
        elif url.path == "/write":
            logger.debug("%s", url)
            self.handle_write()
        elif url.path == "/rewasd":
            logger.debug("%s", url)
            self.handle_rewasd()
        else:
            logger.debug("Ignoring request to " + self.path)
            self.send_error(404)

    def do_PUT(self):
        global logger
        # Acquire the PUT data
        content_length = int(self.headers["Content-Length"])
        raw_data = self.rfile.read(content_length)
        data = json.loads(raw_data, parse_float=float, parse_int=int)

        url = urlparse(self.path)
        if url.path == "/api/configwriter/timer_data":
            with open("timer_data.json", "w") as f:
                json.dump(data, f, indent=4)
            logger.debug("Updated timer_data.json")
        elif url.path == "/api/configwriter/config":
            logger.debug("About to update config.json with %s", data)
            with open("config.json", "r") as f:
                existing = json.load(f)

            # Copy the two settings we don't allow changing by the control panel
            data["host"] = existing["host"]
            data["port"] = existing["port"]
            with open("config.json", "w") as f:
                json.dump(data, f, indent=4)

            # Reload config for rest of program
            global config
            config = readConfig("config.json")
        else:
            logger.debug("Ignoring PUT to " + self.path)
            self.send_error(400)
            return

        self.success_response()

    def success_response(self):
        # Write response
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        body = f"Success"
        self.wfile.write(bytes(body, "utf8"))

    def handle_api(self):
        global logger
        url = urlparse(self.path)
        if url.path == "/api/currency":
            query = parse_qs(urlparse(self.path).query)

            amount = float(query["amount"][0])
            exponent = 0
            if "exponent" in query:
                exponent = int(query["exponent"][0])

            code = query["currency"][0]
            converted = convert_currency(amount, exponent, code)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(bytes(str(converted), "utf-8"))
            return
        elif url.path == "/api/rewasd_queue":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(bytes(rewasd_queue_to_json(), "utf8"))
            return
        elif url.path == "/api/timer":
            # Open timer_data.json
            with open("timer_data.json") as f:
                data = json.load(f)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(data, indent=4), "utf8"))
            return
        elif url.path == "/api/resettimer":
            reset_timer()
            logger.info("Manual timer reset via /api/resettimer")
            self.success_response()
            return
        elif url.path == "/api/config":
            # Open timer_data.json
            with open("config.json") as f:
                data = json.load(f)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(data, indent=4), "utf8"))
            return
        elif url.path == "/api/events":
            with open("logs/events.log") as f:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(bytes(f.read(), "utf-8"))
            return
        elif url.path == "/api/version":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(version_string(), "utf8"))
            return
        logger.error("Unknown API call " + url.path)
        self.send_error(400)

    def handle_event(self):
        global logger
        # Extract query
        query = parse_qs(urlparse(self.path).query)

        global config

        if "train" in query:
            # Some kind of hype train event
            type = query["train"][0]
            if type == "start":
                logger.info("Hype Train Start")
            elif type == "end":
                pass
                # sub_conductor_id = query['sub_conductor'][0]
                # sub_conductor = twitch_id_to_name_cached(sub_conductor_id)
                # bit_conductor_id = query['bit_conductor'][0]
                # bit_conductor = twitch_id_to_name_cached(bit_conductor_id)

                # logger.info("Hype Train End. Sub conductor %s, Bit conductor %s", sub_conductor, bit_conductor)
            elif type == "progress":
                level = query["level"][0]
                progress = query["progress"][0]
                total = query["total"][0]
                logger.info(
                    "Hype Train Progress: Level %s Progress %s Total %s",
                    level,
                    progress,
                    total,
                )
            elif type == "conductor":
                pass
                # sub_conductor_id = query['sub_conductor'][0]
                # sub_conductor = twitch_id_to_name_cached(sub_conductor_id)
                # bit_conductor_id = query['bit_conductor'][0]
                # bit_conductor = twitch_id_to_name_cached(bit_conductor_id)

                # logger.info("Hype Train Conductor. Sub conductor %s, Bit conductor %s", sub_conductor, bit_conductor)
            elif type == "cooldownover":
                logger.info("Hype Train Cooldown Over")
            else:
                # Not a recognized type
                self.send_error(400)
                return
        else:
            # Non-hype train event
            adjust = 0
            points = 0
            points_set = False
            if "bits" in query:
                name = query["name"][0]
                amount = query["bits"][0]
                points = int(config["event"]["per100bits"] * int(amount) / 100)
                message = query["message"][0]
                logger.info(
                    "'"
                    + name
                    + "' cheered "
                    + amount
                    + " bits ("
                    + str(points)
                    + " points): "
                    + message
                )
            elif "sub" in query:
                type = query["sub"][0]
                if type == "self":
                    name = query["name"][0]
                    tier = query["tier"][0]
                    if tier == "Prime":
                        points = int(config["event"]["prime-sub"])
                    elif tier == "Tier 1" or tier == "1000":
                        points = int(config["event"]["t1-sub"])
                    elif tier == "Tier 2" or tier == "2000":
                        points = int(config["event"]["t2-sub"])
                    elif tier == "Tier 3" or tier == "3000":
                        points = int(config["event"]["t3-sub"])
                    else:
                        # Invalid tier, assuming Tier 1
                        points = int(config["event"]["t1-sub"])
                        logger.debug("Have a self sub with a invalid tier" + str(query))
                        logger.info(
                            "Invalid tier of " + tier + " treating it as Tier 1"
                        )
                    months = query["months"][0]
                    message = query["message"][0]

                    logger.info(
                        "'"
                        + name
                        + "' subbed "
                        + tier
                        + " for "
                        + months
                        + " months ("
                        + str(points)
                        + " points): "
                        + message
                    )
                elif type == "gift":
                    gifter = query["gifter"][0]
                    recipient = query["recipient"][0]
                    tier = query["tier"][0]
                    if tier == "Tier 1" or tier == "1000":
                        points = int(config["event"]["t1-sub"])
                    elif tier == "Tier 2" or tier == "2000":
                        points = int(config["event"]["t2-sub"])
                    elif tier == "Tier 3" or tier == "3000":
                        points = int(config["event"]["t3-sub"])
                    else:
                        # Invalid tier, assuming Tier 1
                        points = int(config["event"]["t1-sub"])
                        logger.debug("Have a gift sub with a invalid tier" + str(query))
                        logger.info(
                            "Invalid tier of " + tier + " treating it as Tier 1"
                        )
                    months = query["months"][0]

                    logger.info(
                        "'"
                        + gifter
                        + "' gifted "
                        + tier
                        + " to '"
                        + recipient
                        + "' who now has "
                        + months
                        + " months ("
                        + str(points)
                        + " points)"
                    )

                elif type == "community":
                    name = query["name"][0]
                    quantity = int(query["quantity"][0])
                    tier = query["tier"][0]
                    if tier == "Tier 1" or tier == "1000":
                        points = int(config["event"]["t1-sub"]) * quantity
                    elif tier == "Tier 2" or tier == "2000":
                        points = int(config["event"]["t2-sub"]) * quantity
                    elif tier == "Tier 3" or tier == "3000":
                        points = int(config["event"]["t3-sub"]) * quantity
                    else:
                        # Invalid tier, assuming Tier 1
                        points = int(config["event"]["t1-sub"]) * quantity
                        logger.debug(
                            "Have a community gift sub with a invalid tier" + str(query)
                        )
                        logger.info(
                            "Invalid tier of " + tier + " treating it as Tier 1"
                        )

                    logger.info(
                        "'"
                        + name
                        + "' gifted "
                        + tier
                        + " to "
                        + str(quantity)
                        + " people ("
                        + str(points)
                        + " points)"
                    )

                    pass
                else:
                    logger.debug("Have a sub with invalid type, skipping")
                    self.send_error(400)
                    return

            elif "tip" in query:
                name = query["name"][0]
                amount = float(query["tip"][0])
                amount_after_fees = (
                    amount * (1.0 - config["event"]["tip-fee-percent"] / 100)
                    - config["event"]["tip-fee-fixed"]
                )
                points = int(config["event"]["perdollartip"] * amount_after_fees)
                message = query["message"][0]
                logger.info(
                    "'"
                    + name
                    + "' tipped "
                    + str(amount)
                    + " ("
                    + str(points)
                    + " points): "
                    + message
                )
            elif "hype_chat" in query:
                name = query["name"][0]

                amount = float(query["hype_chat"][0]) / (
                    10 ** int(query["exponent"][0])
                )

                converted_amount = convert_currency(
                    float(query["hype_chat"][0]),
                    int(query["exponent"][0]),
                    query["currency"][0].lower(),
                )

                amount_after_fees = converted_amount * (
                    1.0 - config["event"]["hype-chat-fee-percent"] / 100
                )

                points = int(config["event"]["perdollarhypechat"] * amount_after_fees)
                message = query["message"][0]
                logger.info(
                    "'"
                    + name
                    + "' hype chatted "
                    + str(amount)
                    + " "
                    + query["currency"][0].lower()
                    + " = "
                    + str(converted_amount)
                    + " "
                    + config["event"]["hype-chat-currency"].lower()
                    + " ("
                    + str(points)
                    + " points): "
                    + message
                )
            elif "time" in query:
                direction = 0
                if query["time"][0] == "increase":
                    direction = 1
                elif query["time"][0] == "decrease":
                    direction = -1
                else:
                    # Invalid
                    logger.debug("Event time with invalid value")
                    self.send_response(400)
                    return
                if "amount" not in query:
                    logger.debug("No amount specified")
                    self.send_response(400)
                    return

                today_no_time = datetime.datetime.combine(
                    datetime.date.today(), datetime.time()
                )
                amount = (parse(query["amount"][0]) - today_no_time).total_seconds()

                adjust = int(direction * amount)
                logger.info("Adjust timer by " + str(adjust) + " seconds")

            elif "points" in query:
                direction = 0
                if query["points"][0] == "increase":
                    direction = 1
                elif query["points"][0] == "decrease":
                    direction = -1
                elif query["points"][0] == "set":
                    direction = 1
                    points_set = True
                else:
                    # Invalid
                    logger.debug("Event points with invalid value")
                    self.send_response(400)
                    return

                if "amount" not in query:
                    logger.debug("Points even with no amount")
                    self.send_response(400)
                    return

                points = direction * int(query["amount"][0])
                if points_set:
                    logger.info("Set timer to " + str(points) + " points")
                else:
                    logger.info("Adjust timer by " + str(points) + " points")

            # Read in timer info
            timer_data = {}
            with open("timer_data.json") as f:
                timer_data = json.load(f)

            # Add to total
            if points_set:
                timer_data["points-funded"] = points
            else:
                timer_data["points-funded"] += points
            timer_data["time-adjust"] += adjust

            # Calculate stream end
            stream_start = datetime.datetime.fromisoformat(timer_data["stream-start"])
            stream_end = datetime.datetime.fromisoformat(timer_data["stream-end"])
            percent_funded = (
                timer_data["points-funded"] / timer_data["points-to-fully-fund"]
            )
            time_adjust = datetime.timedelta(seconds=timer_data["time-adjust"])
            timer_start = datetime.timedelta(seconds=timer_data["timer-start"])
            time_fundable = datetime.timedelta(seconds=timer_data["time-fundable"])
            current_end = (
                stream_start
                + timer_start
                + percent_funded * time_fundable
                + time_adjust
            )

            # Do not exceed stream end
            if current_end > stream_end:
                current_end = stream_end

            # Convert back to ISO Format and write out
            timer_data["current-end"] = current_end.isoformat(timespec="milliseconds")

            logger.debug("Timer info is now " + json.dumps(timer_data))

            with open("timer_data.json", "w") as f:
                json.dump(timer_data, f, indent=4)

        self.success_response()

    def handle_keypress(self):
        global logger

        # Extract query
        query = parse_qs(urlparse(self.path).query)

        modifiers_map = {
            "alt": Key.alt,
            "alt_gr": Key.alt_gr,
            "alt_l": Key.alt_l,
            "alt_r": Key.alt_r,
            "ctrl": Key.ctrl,
            "ctrl_l": Key.ctrl_l,
            "ctrl_r": Key.ctrl_r,
            "shift": Key.shift,
            "shift_l": Key.shift_l,
            "shift_r": Key.shift_r,
            "super": Key.cmd,
        }
        key_map = {
            "f1": Key.f1,
            "f2": Key.f2,
            "f3": Key.f3,
            "f4": Key.f4,
            "f5": Key.f5,
            "f6": Key.f6,
            "f7": Key.f7,
            "f8": Key.f8,
            "f9": Key.f9,
            "f10": Key.f10,
            "f11": Key.f11,
            "f12": Key.f12,
            "f13": Key.f13,
            "f14": Key.f14,
            "f15": Key.f15,
            "f16": Key.f16,
            "f17": Key.f17,
            "f18": Key.f18,
            "f19": Key.f19,
            "f20": Key.f20,
        }

        # Determine key to press
        modifiers = []
        if "mod" in query:
            modifiers = [modifiers_map[x] for x in query["mod"]]

        if "key" not in query:
            self.log_message("Requested keypress with no key")
            self.send_error(400)
            return

        keystring = query["key"][0]
        key = ""
        if keystring in "abcdefghijklmnopqrstuvwxyz0123456789":
            key = keystring
        elif keystring in key_map:
            key = key_map[keystring]
        else:
            logger.debug("Unknown key: %s", keystring)
            self.send_error(400)
            return

        repeat = 1
        if "repeat" in query:
            repeat = int(query["repeat"][0])

        delay = 0
        if "delay" in query and repeat != 1:
            delay = int(query["delay"][0]) / 1000

        logger.debug(
            "Pressing key %s with modifiers %s and repeat of %i and delay %i",
            key,
            modifiers,
            repeat,
            delay,
        )

        x = threading.Thread(
            target=keypressWorker, args=(modifiers, key, repeat, delay)
        )
        x.start()

        self.success_response()

    def handle_rewasd(self):
        global logger

        # Extract query
        query = parse_qs(urlparse(self.path).query)

        # Determine device to set
        if "device_id" not in query:
            self.log_message("Requested rewasd with no device_id")
            self.send_error(400)
            return
        device_id = str(query["device_id"][0])

        if "apply" in query:
            # Apply a config
            # Determine path to config file
            if "apply" not in query:
                self.log_message("Requested rewasd with no apply path")
                self.send_error(400)
                return
            apply_path = query["apply"][0]

            # Determine slot to set
            if "slot" not in query:
                self.log_message("Requested rewasd with no slot")
                self.send_error(400)
                return
            slot = query["slot"][0]
            if slot not in ["slot1", "slot2", "slot3", "slot4"]:
                self.log_message("Invalid rewasd slot")
                self.send_error(400)
                return

            x = threading.Thread(
                target=rewasdApplyConfigWorker, args=(device_id, apply_path, slot)
            )
            x.start()

            self.success_response()
            return
        elif "name" in query:
            # Slot swapping
            name = query["name"][0]

            if "duration" not in query:
                self.log_message("Requested rewasd with no duration")
                self.send_error(400)
                return
            duration = int(query["duration"][0])

            if "change_to" not in query:
                self.log_message("Requested rewasd with no change_to")
                self.send_error(400)
                return
            change_to = query["change_to"][0]
            if change_to not in ["slot1", "slot2", "slot3", "slot4"]:
                self.log_message("Invalid rewasd change_to slot")
                self.send_error(400)
                return

            if "return_to" not in query:
                self.log_message("Requested rewasd with no return_to")
                self.send_error(400)
                return
            return_to = query["return_to"][0]
            if return_to not in ["slot1", "slot2", "slot3", "slot4"]:
                self.log_message("Invalid rewasd return_to slot")
                self.send_error(400)
                return

            rewasd_add_to_queue(device_id, name, duration, change_to, return_to)

            self.success_response()
            return

        logger.error("Unknown reWASD call " + str(query))
        self.send_error(400)

    def handle_write(self):
        global logger
        # Extract query
        query = parse_qs(urlparse(self.path).query)

        # Require both filename and data
        if not "filename" in query:
            logger.debug("Missing query parameter filename")
            self.send_error(404)
            return
        if not "data" in query:
            logger.debug("Missing query parameter data")
            self.send_error(404)
            return

        # Optional mode
        mode = "w"
        if "mode" in query:
            if query["mode"][0] == "a":
                mode = "a"
            elif query["mode"][0] != "w":
                logger.debug("Unknown mode parameter '" + query["mode"][0] + "'")
                self.send_error(404)
                return

        filename = query["filename"][0]
        data = query["data"][0]

        # Optional timestamp and per line
        if "log" in query:
            data = datetime.datetime.now().isoformat() + " - " + data + "\n"

        # Actually write to the file
        with open(filename, mode) as w:
            w.write(data)

        if mode == "w":
            logger.debug("'" + filename + "' was overwritten with '" + data + "'")
        elif mode == "a":
            logger.debug("'" + filename + "' was appended with '" + data + "'")

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


def rewasd_select_slot_worker(device_id: str, slot: str):
    rewasdPath = config["rewasd"]["path"]
    if not os.path.isfile(rewasdPath) or not str.endswith(
        rewasdPath, "reWASDCommandLine.exe"
    ):
        logger.error("rewasdPath must target the reWASDCommandLine.exe file")
        return

    # Set reWASD to slot
    cmd = rewasdPath + ' select_slot --id "' + device_id + '" --slot ' + slot
    logger.info("Running command: " + cmd)
    response = subprocess.run(cmd, capture_output=True, text=True).stdout
    if response:
        logger.error(response)
        return


def rewasdApplyConfigWorker(device_id: str, path: str, slot: str):
    rewasdPath = config["rewasd"]["path"]
    if not os.path.isfile(rewasdPath) or not str.endswith(
        rewasdPath, "reWASDCommandLine.exe"
    ):
        logger.error("rewasdPath must target the reWASDCommandLine.exe file")
        return

    # Set reWASD to slot
    cmd = (
        rewasdPath
        + ' apply --id "'
        + device_id
        + '" --path "'
        + path
        + '" --slot '
        + slot
    )
    logger.info("Running command: " + cmd)
    response = subprocess.run(cmd, capture_output=True, text=True).stdout
    if response:
        logger.error(response)


def rewasd_add_to_queue(
    device_id: str, name: str, duration: int, change_to: str, return_to: str
):
    # Acquire queue lock
    with rewasd_lock:
        new_event = ReWASDTimerElement(device_id, name, change_to, return_to, duration)
        # Check if merge-able
        for i in rewasd_queue:
            if i == new_event:
                # Merge
                i.duration += new_event.duration
                new_event = None
                break
        # Insert new item if needed
        if new_event is not None:
            rewasd_queue.append(new_event)

    # Notify processing thread
    rewasd_event.set()


def rewasd_timer_thread():
    global rewasd_in_progress_start
    while True:
        # Ensure there is an item to process, if not wait until there is
        rewasd_lock.acquire()
        if len(rewasd_queue) == 0:
            rewasd_lock.release()
            rewasd_event.wait()
            rewasd_event.clear()
            continue

        logging.debug(f"reWASD Queue: length {len(rewasd_queue)} is {rewasd_queue}")
        now = datetime.datetime.now()
        if rewasd_in_progress_start is None:
            # Fresh event
            logging.debug(f"Call reWASD, turn on slot {rewasd_queue[0].change_to}")
            x = threading.Thread(
                target=rewasd_select_slot_worker,
                args=(rewasd_queue[0].device_id, rewasd_queue[0].change_to),
            )
            x.start()

            # Store current time
            rewasd_in_progress_start = now
            # Sleep for event duration
            logging.debug(f"About to sleep for {rewasd_queue[0].duration} seconds")
            rewasd_lock.release()
            time.sleep(rewasd_queue[0].duration)
            continue

        # Event in progress
        in_progress_duration = (now - rewasd_in_progress_start).total_seconds()
        if in_progress_duration < rewasd_queue[0].duration:
            # Re-sleep, duration not over
            resleep_time = rewasd_queue[0].duration - in_progress_duration
            logging.debug(f"Re-sleep for {resleep_time}")
            rewasd_lock.release()
            time.sleep(resleep_time)
            continue

        # Finish event
        if len(rewasd_queue) > 1:
            # Move straight to next event in queue
            rewasd_queue.pop(0)
            logging.debug(
                f"Call reWASD change to new event {rewasd_queue[0].change_to}"
            )
            x = threading.Thread(
                target=rewasd_select_slot_worker,
                args=(rewasd_queue[0].device_id, rewasd_queue[0].change_to),
            )
            x.start()

            rewasd_in_progress_start = now
            # Sleep for event duration
            logging.debug(f"About to sleep for {rewasd_queue[0].duration} seconds")
            rewasd_lock.release()
            time.sleep(rewasd_queue[0].duration)
            continue

        # Queue will now be empty, go to return_to
        logging.debug(f"Call reWASD to return too {rewasd_queue[0].return_to}")
        x = threading.Thread(
            target=rewasd_select_slot_worker,
            args=(rewasd_queue[0].device_id, rewasd_queue[0].return_to),
        )
        x.start()
        rewasd_queue.pop(0)
        rewasd_lock.release()
        rewasd_in_progress_start = None


def rewasd_queue_to_json():
    result = dict()

    if rewasd_in_progress_start is None:
        result["current_start"] = None
    else:
        result["current_start"] = rewasd_in_progress_start.isoformat(
            timespec="milliseconds"
        )

    result["events"] = [[x.name, x.duration] for x in rewasd_queue]

    return JSONEncoder(indent=4).encode(result)


@dataclass
class ReWASDTimerElement:
    device_id: str
    name: str
    change_to: str
    return_to: str
    duration: int

    def __eq__(self, other):
        return self.name == other.name


rewasd_queue = list()
rewasd_lock = threading.Lock()
rewasd_event = threading.Event()
rewasd_in_progress_start = None
rewasd_thread = threading.Thread(target=rewasd_timer_thread, args=())
rewasd_thread.start()


def convert_currency(amount: float, exp: int, currency_code: str):
    amount = amount / (10**exp)
    global currency_conversion
    currency_rate = float(
        currency_conversion[config["event"]["hype-chat-currency"].lower()][
            currency_code
        ]
    )
    return amount / currency_rate


def readConfig(filename):
    with open(filename) as f:
        config = json.load(f)

        # Convert inputs into datetime and timedeltas as appropriate

        config["timer"]["stream-start"] = parse(config["timer"]["stream-start"])

        # dateutil.parser will assume today's date if given something like "30s", subtract
        # off today's date to get a correct duration
        today_no_time = datetime.datetime.combine(
            datetime.date.today(), datetime.time()
        )
        config["timer"]["timer-start"] = (
            parse(config["timer"]["timer-start"]) - today_no_time
        )
        config["timer"]["time-fundable"] = (
            parse(config["timer"]["time-fundable"]) - today_no_time
        )

        return config


def ensureTimerSetup(config):
    if os.path.exists("timer_data.json"):
        with open("timer_data.json") as f:
            timer_data = json.load(f)

            # Convert into datetimes
            timer_data["stream-start"] = parse(timer_data["stream-start"])
            timer_data["stream-end"] = parse(timer_data["stream-end"])
            timer_data["current-end"] = parse(timer_data["current-end"])

            now = datetime.datetime.now()
            if now < timer_data["current-end"]:
                print(
                    "Since current time is before end in timer_data.json, assuming script restarted during stream"
                )
                return
    reset_timer()


def reset_timer():
    global config
    # No existing timer data or expired
    timer_data = {}
    timer_data["stream-start"] = config["timer"]["stream-start"].isoformat()
    timer_data["stream-end"] = (
        config["timer"]["stream-start"]
        + config["timer"]["timer-start"]
        + config["timer"]["time-fundable"]
    ).isoformat()
    timer_data["current-end"] = (
        config["timer"]["stream-start"] + config["timer"]["timer-start"]
    ).isoformat()
    timer_data["points-funded"] = 0
    timer_data["points-to-fully-fund"] = config["timer"]["points-to-fully-fund"]
    timer_data["time-adjust"] = 0
    timer_data["timer-start"] = config["timer"]["timer-start"].total_seconds()
    timer_data["time-fundable"] = config["timer"]["time-fundable"].total_seconds()

    with open("timer_data.json", "w") as f:
        json.dump(timer_data, f, indent=4)


def version_string():
    return "0.2.0"


def setup_logging():
    # Ensure there is a logs directory
    os.makedirs("logs", exist_ok=True)

    # Setup a rotating debug log
    debug_handler = logging.handlers.TimedRotatingFileHandler(
        filename="logs/debug.log", when="d", interval=1, backupCount=10
    )
    debug_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    debug_handler.setFormatter(debug_formatter)
    debug_handler.setLevel(logging.DEBUG)

    # Setup rotating event log
    event_handler = logging.handlers.TimedRotatingFileHandler(
        filename="logs/events.log",
        when="d",
        interval=1,
    )
    event_formatter = logging.Formatter("%(asctime)s - %(message)s")
    event_handler.setFormatter(event_formatter)
    event_handler.setLevel(logging.INFO)

    # Attach handlers
    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(debug_handler)
    logger.addHandler(event_handler)
    return logger


def get_currency_conversion(config):
    base_currency = config["event"]["hype-chat-currency"].lower()

    mirrors = [
        f"https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{base_currency}.min.json",
        f"https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{base_currency}.json",
        f"https://raw.githubusercontent.com/fawazahmed0/currency-api/1/latest/currencies/{base_currency}.min.json",
        f"https://raw.githubusercontent.com/fawazahmed0/currency-api/1/latest/currencies/{base_currency}.json",
    ]
    # Timeout controls how many seconds to wait before first byte of
    # response. This is not limiting the total connection time if it
    # longer
    timeout = 1

    for url in mirrors:
        try:
            # Initiate request
            logging.debug(f"Connecting to {url}")
            r = httpx.get(url, timeout=timeout)

            # Ensure it went well
            r.raise_for_status()

            # Success
            logging.info(f"Retrieved currency data from {url}")
            return json.loads(r.text)
        except httpx.RequestError as exc:
            logging.error(f"An error occurred while requesting {exc.request.url!r}.")
        except httpx.HTTPStatusError as exc:
            logging.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )

    logging.critical("Unable to download currency conversion from anywhere. Aborting")
    print("Unable to download currency conversion from anywhere. Aborting")

    sys.exit(1)


def startServer():
    global logger
    logger = setup_logging()
    global config
    config = readConfig("config.json")
    ensureTimerSetup(config)

    if "rewasd" in config and "path" in config["rewasd"]:
        rewasdPath = config["rewasd"]["path"]
        if not os.path.isfile(rewasdPath) or not str.endswith(
            rewasdPath, "reWASDCommandLine.exe"
        ):
            print(
                "rewasdPath must target the reWASDCommandLine.exe file itself. Falling back to default install location."
            )
            config["rewasd"]["path"] = "C:/Program Files/reWASD/reWASDCommandLine.exe"
        else:
            print("reWASDCommandLine.exe found at path: " + rewasdPath)
    else:
        print(
            "rewasdPath not found in loaded config. falling back to default install location."
        )
        config["rewasd"]["path"] = "C:/Program Files/reWASD/reWASDCommandLine.exe"

    global currency_conversion
    currency_conversion = get_currency_conversion(config)

    print("WritingHTTPServer " + version_string() + " by Number6174")
    print("Server started on http://" + config["host"] + ":" + str(config["port"]))
    print("Use CTRL+C to stop")

    logger.info(
        "Server startup. Version "
        + version_string()
        + " listening on "
        + config["host"]
        + ":"
        + str(config["port"])
    )

    # Setup server
    handler = WritingHttpRequestHandler
    server = http.server.HTTPServer((config["host"], config["port"]), handler)

    # Start the server
    server.serve_forever()


if __name__ == "__main__":
    startServer()
