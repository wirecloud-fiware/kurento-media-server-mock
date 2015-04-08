import websocket
import json
import time
from threading import Thread

protocol_local = "ws"
protocol_remote = "ws"

base_local = "localhost"
base_remote = "130.206.81.33"

port_local = "8889"
port_remote = "8888"

path_local = ""
path_remote = "crowddetector"

URL_REMOTE = "{}://{}:{}/{}".format(protocol_remote, base_remote, port_remote, path_local)
URL_LOCAL = "{}://{}:{}/{}".format(protocol_local, base_local, port_local, path_local)


def webs(url=URL_LOCAL):
    def aux1(f):
        def aux(*args, **kargs):
            ws = websocket.WebSocket()
            ws.connect(url)
            # return f(ws, *args, **kargs)
            res = f(ws, *args, **kargs)
            ws.close()
            return res
        return aux
    return aux1


def wrap_ws(url, f):
    @webs(url)
    def aux(ws):
        f(ws)
    return aux


def remote_wrap(f):
    return wrap_ws(URL_REMOTE, f)


def local_wrap(f):
    return wrap_ws(URL_LOCAL, f)


def send(ws, msg):
    print("Sending: {}".format(msg))
    ws.send(msg)
    print("End send")


def recv(ws):
    a = time.time()
    result = ws.recv()
    print("Received: {}".format(result))
    print("Time: {}".format(time.time() - a))
    return result


def sendrecv(ws, msg):
    print("")
    send(ws, msg)
    return recv(ws)


def createMedia(ws, i=1):
    msg = {"id": i, "method": "create", "params": {
        "type": "MediaPipeline", "constructorParams": {}}, "jsonrpc": "2.0"}
    return sendrecv(ws, json.dumps(msg))


def createWebRtc(ws, sid, mpipe, i=2):
    msg = {"id": i, "method": "create", "params": {
        "type": "WebRtcEndpoint", "constructorParams": {
            'mediaPipeline': mpipe}, "sessionId": sid}, "jsonrpc": "2.0"}
    return sendrecv(ws, json.dumps(msg))


def createPlayer(ws, sid, mpipe, url, i=0):
    msg = {"id": i, "method": "create", "params": {
        "type": "PlayerEndpoint", "constructorParams": {
            'mediaPipeline': mpipe, "uri": url}, "sessionId": sid}, "jsonrpc": "2.0"}
    return sendrecv(ws, json.dumps(msg))


def createCrowdDetector(ws, sid, mpipe, i=3):
    roi = {
        'id': 'roi1',
        'points': [{'x': 0.8, 'y': 0.7},
                   {'x': 0.6, 'y': 0.6},
                   {'x': 0.4, 'y': 0.4}],
        'regionOfInterestConfig': {
            'occupancyLevelMin': 10,
            'occupancyLevelMed': 35,
            'occupancyLevelMax': 65,
            'occupancyNumFramesToEvent': 5,
            'fluidityLevelMin': 10,
            'fluidityLevelMed': 35,
            'fluidityLevelMax': 65,
            'fluidityNumFramesToEvent': 5,
            'sendOpticalFlowEvent': False,
            'opticalFlowNumFramesToEvent': 3,
            'opticalFlowNumFramesToReset': 3,
            'opticalFlowAngleOffset': 0
        }
    }
    msg = {"id": i, "method": "create", "jsonrpc": "2.0", "params": {
        "type": "CrowdDetectorFilter", "constructorParams": {
            'rois': [roi], 'mediaPipeline': mpipe}, "sessionId": sid}}
    return sendrecv(ws, json.dumps(msg))


def invoke(ws, sid, operation, f, t, i=4):
    msg = {"id": i, "method": "invoke", "jsonrpc": "2.0", "params": {
        "operation": operation, "object": f, "sessionId": sid,
        "operationParams": t}}
    return sendrecv(ws, json.dumps(msg))


def subscribe(ws, sid, typ, obj, i=6):
    msg = {"id": i, "method": "subscribe", "jsonrpc": "2.0", "params": {
        "type": typ, "object": obj, "sessionId": sid}}
    return sendrecv(ws, json.dumps(msg))


def release(ws, sid, mpipe, i=7):
    msg = {"id": i, "method": "release", "jsonrpc": "2.0", "params": {
        "object": mpipe, "sessionId": sid}}
    return sendrecv(ws, json.dumps(msg))


def connect(ws, sid, i=2):
    msg = {'id': 2, 'method': 'connect', 'jsonrpc': '2.0', 'params': {
        'sessionId': sid}}
    return sendrecv(ws, json.dumps(msg))


def get_value(v):
    return json.loads(v)['result']['value']


def start_data(ws):
    m = createMedia(ws, 1)
    m = json.loads(m)
    sid = m['result']['sessionId']
    mpipe = m['result']['value']
    webrtc = get_value(createWebRtc(ws, sid, mpipe, 2))
    crowd = get_value(createCrowdDetector(ws, sid, mpipe, 3))
    invoke(ws, sid, "connect", webrtc, {'sink': crowd}, 4)
    invoke(ws, sid, "connect", crowd, {'sink': webrtc}, 5)
    subscribe(ws, sid, "CrowdDetectorOccupancy", crowd, 6)
    subscribe(ws, sid, "CrowdDetectorFluidity", crowd, 7)
    subscribe(ws, sid, "CrowdDetectorDirection", crowd, 8)
    invoke(ws, sid, "processOffer", webrtc, {'offer': 'test'}, 9)
    release(ws, sid, mpipe, 10)


def getvideo_data(ws, url="http://test.com"):
    m = createMedia(ws, 1)
    m = json.loads(m)
    sid = m['result']['sessionId']
    mpipe = m['result']['value']
    webrtc = get_value(createWebRtc(ws, sid, mpipe, 2))
    mplayer = get_value(createPlayer(ws, sid, mpipe, url, 3))
    invoke(ws, sid, "connect", mplayer, {'sink': webrtc}, 5)
    invoke(ws, sid, "setMaxVideoRecvBandwidth", webrtc, {'maxVideoRecvBandwidth': 0}, 6)
    invoke(ws, sid, "setMaxVideoSendBandwidth", webrtc, {'maxVideoSendBandwidth': 9999999}, 7)
    invoke(ws, sid, "setMinVideoSendBandwidth", webrtc, {'minVideoSendBandwidth': 9999999}, 8)
    subscribe(ws, sid, 'EndOfStream', mplayer, 9)
    invoke(ws, sid, 'play', mplayer, {}, 10)
    invoke(ws, sid, "processOffer", webrtc, {'offer': 'test'}, 11)
    release(ws, sid, mpipe, 12)

def getvideo_data_filter(ws, url="http://test.com"):
    m = createMedia(ws, 1)
    m = json.loads(m)
    sid = m['result']['sessionId']
    mpipe = m['result']['value']
    webrtc = get_value(createWebRtc(ws, sid, mpipe, 2))
    mplayer = get_value(createPlayer(ws, sid, mpipe, url, 3))
    invoke(ws, sid, "connect", mplayer, {'sink': webrtc}, 5)
    invoke(ws, sid, "setMaxVideoRecvBandwidth", webrtc, {'maxVideoRecvBandwidth': 0}, 6)
    invoke(ws, sid, "setMaxVideoSendBandwidth", webrtc, {'maxVideoSendBandwidth': 9999999}, 7)
    invoke(ws, sid, "setMinVideoSendBandwidth", webrtc, {'minVideoSendBandwidth': 9999999}, 8)
    subscribe(ws, sid, 'EndOfStream', mplayer, 9)
    invoke(ws, sid, 'play', mplayer, {}, 10)
    crowd = get_value(createCrowdDetector(ws, sid, mpipe, 4))
    invoke(ws, sid, "connect", crowd, {'sink': webrtc}, 6)
    subscribe(ws, sid, "CrowdDetectorOccupancy", crowd, 7)
    subscribe(ws, sid, "CrowdDetectorFluidity", crowd, 8)
    subscribe(ws, sid, "CrowdDetectorDirection", crowd, 9)
    invoke(ws, sid, "processOffer", webrtc, {'offer': 'test'}, 11)
    release(ws, sid, mpipe, 12)


remote_start = remote_wrap(start_data)
local_start = local_wrap(start_data)

remote_getvideo = remote_wrap(getvideo_data)
local_getvideo = local_wrap(getvideo_data)

remote_getvideo_filter = remote_wrap(getvideo_data_filter)
local_getvideo_filter= local_wrap(getvideo_data_filter)


def main(elocal=True, eremote=False):
    execfs = lambda x: list(map(lambda y: y(), x))
    local = [local_start, local_getvideo, local_getvideo_filter]
    remote = [remote_start, remote_getvideo, remote_getvideo_filter]

    if elocal:
        execfs(local)
    if eremote:
        execfs(remote)


if __name__ == "__main__":
    main()
