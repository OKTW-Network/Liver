import asyncio
import json
import logging
import websockets

from uuid import uuid4 as generateUUID

logging.basicConfig()

channels = {}

config = json.load(open("./config.json", "r"))


class User:

    def __init__(self, ws, name=None, uuid=None):
        self.name = name or ""
        self.uuid = uuid or str(generateUUID())
        self.channel = ""
        self.ws = ws

    async def sendData(self, data):
        await self.ws.send(json.dumps(data))

    async def sendError(self, msg=None):
        await self.sendData({"type": "error", "msg": msg or "挖勒喔依"})

    async def sendConnectedMessage(self):
        await self.sendData({"type": "connected", "uuid": self.uuid})

    def setName(self, name):
        self.name = name

    async def sendBulletScreen(self, user, msg):
        await self.sendData({
            "type": "bulletScreenMessage"
            "msg": msg,
            "sentFrom": user.name})

    async def receiveBulletScreen(self, msg):
        print("[Info] Recvive message Channel : %s  User : %s  UUID : %s  Message : %s" % (
            self.channel, self.name, self.uuid, msg))
        if self.channel != "":
            for user in channels[self.channel].viewers:
                await user.sendBulletScreen(self, msg)

    async def joinChannel(self, channelName):
        if channelName not in channels:
            channels[channelName] = Channel(channelName)

        for channel in channels:
            if channels[channel].userInChannel(self):
                channels[channel].removeViewer(self)

        channels[channelName].addViewer(self)

        self.channel = channelName

        await user.sendData({"type": "channelJoined", "channel": channels[self.channel]})

    def getChannel(self):
        if self.channel != "":
            return(channels[self.channel])
        else:
            return(None)

    def disconnect(self):
        for channel in channels:
            if channels[channel].userInChannel(self):
                channels[channel].removeViewer(self)


class Channel:

    def __init__(self, name):
        self.name = name
        self.viewers = []

    async def broadcastChannelData(self):
        for viewer in self.viewers:
            await viewer.sendData(self.getChannelData())

    async def addViewer(self, user):
        if user.uuid in map(getUserUUID, self.viewers):
            return(False)
        else:
            self.viewers.append(user)
            return(True)

    async def removeViewer(self, user):
        if user.uuid in map(getUserUUID, self.viewers):
            self.viewers.remove(user)
            return(True)
        else:
            return(False)

    def getUserInChannel(self, user):
        if user.uuid in map(getUserUUID, self.viewers):
            return(True)
        else:
            return(False)

    def getViewers(self):
        return(self.viewers)

    def getNowViewerCount(self):
        return(len(self.viewers))

    def getChannelData(self):
        return({
            "type": "channelData",
            "name": self.name,
            "nowViewerCount": self.getNowViewerCount()
        })


def getUserUUID(user):
    return(user.uuid)


async def connect(ws, path):
    user = User(ws)
    try:
        await user.sendConnectedMessage()
        async for data in ws:
            try:
                data = json.loads(data)
                if "method" in data:
                    if data["method"] == "joinChannel":
                        if "channelName" in data:
                            user.joinChannel(data["channelName"])
                        else:
                            user.sendError("missingData")
                    elif data["method"] == "sendBulletMessage":
                        if "msg" in data:
                            user.receiveBulletScreen(data["msg"])
                        else:
                            user.sendError("missingData")
                    elif data["method"] == "getChannelData":
                        channel = user.getChannel()
                        if channel == None:
                            user.sendError("notInAnyChannel")
                        else:
                            user.sendData(channel.getChannelData())

            except:
                await user.sendError()
    finally:
        user.disconnect()


def init():
    print("[Info] WebSocket server started at %s:%d" %
          (config["ws"]["host"], config["ws"]["port"]))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(connect, config["ws"]["host"], config["ws"]["port"]))
    asyncio.get_event_loop().run_forever()
