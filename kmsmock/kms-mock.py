#!/usr/bin/env python2

try:
    from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
except ImportError:
    from kmsmock.SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
import json
import os
from time import sleep
from uuid import uuid4
from signal import SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, signal

colors = {"RED": '\033[91m',
          "BLUE": '\033[94m',
          "RESET": '\033[0m',
          "OK": '\033[92m',
          "PINK": '\033[95m'}


def print_with_color(msg, color):
    """Print with color and tabs (reset at the end)"""
    print("%s%s%s" % (color, msg, colors.get("RESET")))


def addToSignals():
    """Add a handler to the signals"""
    for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
        signal(sig, cleanFromSignal)


def cleanFromSignal(*args):
    print_with_color("\nServer stopped.", colors['OK'])
    server.close()
    exit(0)


class KurMockServer(WebSocket):
    last_id = 0
    sid = None
    mpipe_id = None
    webrtc_id = None
    crowd_id = None
    occ_id = None
    flu_id = None
    dir_id = None

    pids = []
    send_event = False

    def send(self, msg):
        print_with_color("[-] %s" % msg, colors.get("BLUE"))
        self.sendMessage(json.dumps(msg))

    def check_sid(self, sid):
        return sid == self.sid

    def create_base(self, i, result=None):
        if result is None:
            result = {}
        sid = {} if not self.sid else {'sessionId': self.sid}
        result.update(sid)
        return {'id': i, "jsonrpc": "2.0", "result": result}

    def create_error(self, i):
        return {'id': i, "jsonrpc": "2.0", "error": {"code": 40001, "data": {
            "type": "MYOWN_ERROR"}, "message": "This is an error"}}

    def onEvent(self, i, source, typ, obj, subs):
        levelperc_admit = ["occupancy", "fluidity"]
        typename = typ[13:].lower()
        level = {typename + "Level": 3} if typename in levelperc_admit else {}
        perc = {typename + "Percentage": 80.0} if typename in levelperc_admit else {}
        dr = {'directionAngle': 20.0} if typename == "direction" else {}
        v = {"id": i, "jsonrpc": "2.0", "method": "onEvent", "params": {'value': {}}}
        par = {'object': obj, 'subscription': subs, 'type': typ, 'data': {
            'source': source, 'type': typ, 'roiID': 'roi1'}}
        v['params']['value'].update(par)
        v['params']['value']['data'].update(level)
        v['params']['value']['data'].update(perc)
        v['params']['value']['data'].update(dr)
        # v['params'].update(sid)
        return v

    def createMediaPipeline(self, msg):
        self.sid = str(uuid4())
        self.mpipe_id = "{}_MediaPipeline".format(uuid4())
        return self.create_base(msg['id'], {'value': self.mpipe_id})

    def createWebRtcEndpoint(self, msg, mpipe):
        self.webrtc_id = "{}_WebRtcEndpoint".format(uuid4())
        return self.create_base(msg['id'], {'value': "{}/{}".format(mpipe, self.webrtc_id)})

    def createCrowdDetectorFilter(self, msg, mpipe):
        self.crowd_id = "{}_CrowdDetectorFilter".format(uuid4())
        return self.create_base(msg['id'], {'value': '{}/{}'.format(mpipe, self.crowd_id)})

    def createPlayer(self, msg, mpipe):
        self.player_id = "{}_PlayerEndpoint".format(uuid4())
        # return self.create_error(msg['id'])
        return self.create_base(msg['id'], {'value': '{}/{}'.format(mpipe, self.player_id)})

    def handleSubscribe(self, t):
        if t == 'CrowdDetectorOccupancy':
            self.occ_id = str(uuid4())
            return self.occ_id
        elif t == 'CrowdDetectorFluidity':
            self.flu_id = str(uuid4())
            return self.flu_id
        elif t == 'CrowdDetectorDirection':
            self.dir_id = str(uuid4())
            return self.dir_id
        elif t == 'EndOfStream':
            return str(uuid4())
        return None

    def create(self, msg):
        t = msg['params']['type']
        mpipe = msg['params']['constructorParams'].get('mediaPipeline')
        rmsg = None
        if t == 'MediaPipeline':
            rmsg = self.createMediaPipeline(msg)
        elif t == 'WebRtcEndpoint':
            rmsg = self.createWebRtcEndpoint(msg, mpipe)
        elif t == 'CrowdDetectorFilter':
            rmsg = self.createCrowdDetectorFilter(msg, mpipe)
            ps = msg['params']['constructorParams']['rois'][0]['points']
            self.send_event = ps == [{'x': 9.0, 'y': 7.0}, {'x': 1.0, 'y': 1.0}]
        elif t == 'PlayerEndpoint':
            rmsg = self.createPlayer(msg, mpipe)
        self.send(rmsg)

    def invoke(self, msg):
        t = msg['params']['operation']
        rmsg = None
        if t in ['connect', 'setMaxVideoRecvBandwidth', 'setMaxVideoSendBandwidth', 'setMinVideoSendBandwidth', 'play']:
            rmsg = self.create_base(msg['id'], {'value': None})
        elif t == 'processOffer':
            rmsg = self.create_base(msg['id'], {'value': 'v=0\r\ns=Kurento Media Server\r\nc=IN IP4 0.0.0.0\r\nt=0 0\r\n'})
        self.send(rmsg)

    def subscribe(self, msg):
        t = msg['params']['type']
        i = self.handleSubscribe(t)
        if self.send_event and t.startswith("CrowdDetector"):
            pid = os.fork()
            if pid == 0:
                sleep(1)
                l = self.onEvent(msg['id'], msg['params']['object'], str(t), msg['params']['object'], i)
                self.send(l)
                os._exit(0)
            else:
                self.pids.append(pid)

        rmsg = self.create_base(msg['id'], {'value': i})
        self.send(rmsg)

    def release(self, msg):
        for p in self.pids:
            os.kill(p, 9)
        self.pids = []
        self.send(self.create_base(msg['id']))

    def handleMessage(self):
        if self.data is None:
            self.data = ""
        else:
            print_with_color("[+] " + str(self.data), colors['PINK'])
            msg = json.loads(str(self.data))
            self.last_id = msg['id']
            if msg.get('method') == 'create':
                self.create(msg)
            elif msg.get('method') == 'invoke':
                self.invoke(msg)
            elif msg.get('method') == 'subscribe':
                self.subscribe(msg)
            elif msg.get('method') == 'release':
                self.release(msg)

    def handleConnected(self):
        self.connected = True
        print_with_color("[++] Connected: " + str(self.address), colors['OK'])

    def handleClose(self):
        self.connected = False
        print_with_color("[--] Disconnected: " + str(self.address), colors['RED'])

port = 8889
server = SimpleWebSocketServer('', port, KurMockServer)
print_with_color("Server started in localhost:{}".format(port), colors['OK'])
try:
    server.serveforever()
except KeyboardInterrupt:
    cleanFromSignal()
