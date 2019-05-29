import asyncio
import json
import logging
import websockets

logging.basicConfig()

users = set()

config = json.load(open("./config.json","r"))

async def register(ws):
    users.add(ws)

async def unregister(ws):
    users.remove(ws)

async def sendBulletScreen(channel,user,msg):
    if users:
        data = json.dumps({"status":"MSG_RECV","msg":msg,"user":user,"channel":channel})
        await asyncio.wait([user.send(data) for user in users])

async def connect(ws, path):
    await register(ws)
    try:
        await ws.send(json.dumps({"status":"CONNECTED","msg":"Hello user."}))
        async for data in ws:
            ws.send("Recv")
            try:
                data = json.loads(data)
                if "user" in data and "msg" in data:
                    print("[Info] Recvive message Channel : %s  User : %s  Message : %s" % (data["channel"],data["user"],data["msg"]))
                    await sendBulletScreen(data["user"],data["msg"])
                    await ws.send(json.dumps({"status":"MSG_SENT","msg":"Message sent."}))
                else:
                    await ws.send(json.dumps({"status":"OEOE","msg":"Triggered"}))    
            except:
                await ws.send(json.dumps({"status":"OEOE","msg":"Triggered"}))
    finally:
        await unregister(ws)

def init():
    print("[Info] WebSocket server started at %s:%d" % (config["ws"]["host"],config["ws"]["port"]))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(connect, config["ws"]["host"], config["ws"]["port"]))
    asyncio.get_event_loop().run_forever()
