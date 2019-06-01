import asyncio
import json
import logging
import websockets
import logging
logger = logging.getLogger('websockets')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

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
        print("[Info] User %s joined." % (self.uuid))

    async def sendData(self, data):
        await self.ws.send(json.dumps(data))

    async def sendError(self, msg=None):
        await self.sendData({"type": "error", "msg": msg or "挖勒喔依"})

    async def sendConnectedMessage(self):
        await self.sendData({"type": "connected", "uuid": self.uuid})

    def getName(self):
        return(self.name)

    async def setName(self, name):
        self.name = name
        await self.sendData({"type": "nameSet", "name": self.name})
        print("[Info] User %s set name to %s ." % (self.uuid,self.name))

    async def sendBulletScreen(self, user, msg, uuid):
        await self.sendData({
            "type": "bulletScreenMessage",
            "msg": msg,
            "sentFrom": user.name,
            "uuid": uuid})

    async def receiveBulletScreen(self, msg):
        print("[Info] Recvive message Channel : %s  User : %s  UUID : %s  Message : %s ." % (
            self.channel, self.name, self.uuid, msg))
        if self.channel != "":
            for user in channels[self.channel].viewers:
                await user.sendBulletScreen(self, msg, str(generateUUID()))

    async def joinChannel(self, channelName):
        if channelName not in channels:
            channels[channelName] = Channel(channelName)

        for channel in channels:
            if channels[channel].isUserInChannel(self):
                await channels[channel].removeViewer(self)

        await channels[channelName].addViewer(self)

        self.channel = channelName

        await self.sendData({"type": "channelJoined", "channel": channels[self.channel].getChannelData()})
        
        print("[Info] User %s join channel %s ." % (self.uuid,self.channel))
        
        for user in channels[self.channel].viewers:
            await user.sendData(channels[self.channel].getChannelData())

    def getChannel(self):
        if self.channel != "":
            return(channels[self.channel])
        else:
            return(None)

    async def disconnect(self):
        for channel in channels:
            if channels[channel].isUserInChannel(self):
                await channels[channel].removeViewer(self)
                
        print("[Info] User %s disconnected." % (self.uuid))

        for user in channels[self.channel].viewers:
            await user.sendData(channels[self.channel].getChannelData())


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

    def isUserInChannel(self, user):
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
                            await user.joinChannel(data["channelName"])
                        else:
                            await user.sendError("missingData")
                    if data["method"] == "setName":
                        if "name" in data:
                            await user.setName(data["name"])
                        else:
                            await user.sendError("missingData")
                    elif data["method"] == "sendBulletMessage":
                        if "msg" in data:
                            if user.getName() == "":
                                await user.sendError("nameNotSet")
                            else:
                                await user.receiveBulletScreen(data["msg"])
                        else:
                            await user.sendError("missingData")
                    elif data["method"] == "getChannelData":
                        channel = user.getChannel()
                        if channel == None:
                            await user.sendError("notInAnyChannel")
                        else:
                            await user.sendData(channel.getChannelData())

            except:
                import traceback
                traceback.print_exc()
                await user.sendError()
    finally:
        await user.disconnect()


def init():
    print("[Info] WebSocket server started at %s:%d" %
          (config["ws"]["host"], config["ws"]["port"]))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(connect, config["ws"]["host"], config["ws"]["port"]))
    asyncio.get_event_loop().run_forever()
