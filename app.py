import threading
import os
import sys
import json

if not os.path.exists("./config.json"):
    print("[Error] Config file not found , please copy and edit config.example.json to config.json")
    sys.exit()

from libs import ws

config = json.load(open("./config.json","r"))

threadCount = 0


if config["ws"]["enabled"]:
    threadCount = threadCount + 1
    ws = threading.Thread(target=ws.init)
    ws.daemon = True
    ws.start()

while True:
    tmp = threadCount
    if config["ws"]["enabled"]:
        if not ws.isAlive:
            tmp = tmp - 1
    if tmp == 0:
        break