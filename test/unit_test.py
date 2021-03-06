#!/usr/bin/python3
import unittest
from plumbum import local, cli, BG
from plumbum.commands.processes import ProcessExecutionError

build_hlpr_cmd = local["python3"]["test/build_helper.py"]
f = None

def startWebsocketSrv():
    global f
    f = local["python2"]["test/test_server.py"] & BG

def killWebsocketSrv():
    global f
    if not f is None:
        f.proc.kill()
        f.proc.stdout.close()
        f.proc.stdin.close()
        f.proc.stderr.close()
        f = None


def getNginxPID():
    chain = local["pgrep"]["nginx"] | local["tail"]["-n1"]
    pid = int(chain())
    return pid

def startNginx():
    try:
        local["pkill"]["-9", "nginx"]()
    except ProcessExecutionError:
        pass
    build_hlpr_cmd("conf")
    build_hlpr_cmd("start_nginx")
    return getNginxPID()

def getTotalMem(pid):
    chain = local["pmap"][pid] | local["sed"]["-n", 's/total\\ *\\(.*\\)/\\1/p']
    out = chain()
    return (int(out.replace('K','')))

class TestWebStat(unittest.TestCase):
    def regularCheck(self, sent_frames, sent_payload, 
                     logged_frames, logged_payload, 
                     connections, 
                     reported_frames, reported_payload):
        self.assertEqual(sent_frames, reported_frames)
        self.assertEqual(sent_frames, logged_frames)
        self.assertEqual(logged_frames, reported_frames)
        self.assertEqual(sent_payload, reported_payload)
        self.assertEqual(sent_payload, logged_payload)
        self.assertEqual(logged_payload, reported_payload)
        self.assertEqual(connections, 0)
    
    def testSimple(self):
        startWebsocketSrv()
        self_run_cmd = local["python3"]['test/ws_test.py'] \
                       [
                       "-h", "127.0.0.1:8080",
                       "-w",
                       "--fps", 3,
                       "--seconds", 1,
                       "--connections", 5,
                       "--packet", 10,
                       "--instances", 5,
                       "--robot_friendly"
                       ]
        self.regularCheck(*[int(x) for x in self_run_cmd().split()])
        killWebsocketSrv()

    def test500Cons(self):
        startWebsocketSrv()
        self_run_cmd = local["python3"]['test/ws_test.py'] \
                       [
                       "-h", "127.0.0.1:8080",
                       "-w",
                       "--fps", 3,
                       "--seconds", 5,
                       "--connections", 5,
                       "--packet", 100,
                       "--instances", 100,
                       "--robot_friendly"
                       ]
        self.regularCheck(*[int(x) for x in self_run_cmd().split()])
        killWebsocketSrv()

    def testLongRun500Cons(self):
        startWebsocketSrv()
        self_run_cmd = local["python3"]['test/ws_test.py'] \
                       [
                       "-h", "127.0.0.1:8080",
                       "-w",
                       "--fps", 3,
                       "--seconds", 60,
                       "--connections", 5,
                       "--packet", 100,
                       "--instances", 100,
                       "--robot_friendly"
                       ]
        self.regularCheck(*[int(x) for x in self_run_cmd().split()])
        killWebsocketSrv()

    def testLargePackets(self):
        startWebsocketSrv()
        self_run_cmd = local["python3"]['test/ws_test.py'] \
                       [
                       "-h", "127.0.0.1:8080",
                       "-w",
                       "--fps", 10,
                       "--seconds", 0,
                       "--connections", 5,
                       "--packet", 1000000,
                       "--instances", 2,
                       "--robot_friendly"
                       ]
        self.regularCheck(*[int(x) for x in self_run_cmd().split()])
        killWebsocketSrv()

    def testMemoryLeak(self):
        startWebsocketSrv()
        pid = startNginx()
        memory = local["pmap"]
        memBefore = getTotalMem(pid)
        self_run_cmd = local["python3"]['test/ws_test.py'] \
                       [
                       "-h", "127.0.0.1:8080",
                       "-w",
                       "--fps", 3,
                       "--seconds", 60,
                       "--connections", 5,
                       "--packet", 3000,
                       "--instances", 100,
                       "--robot_friendly",
                       "--keepNginx"
                       ]
        Runs = 5
        memRuns = set()
        for i in range(0, Runs):
            print("{} run".format(i+1))
            self_run_cmd()
            self.assertEqual(pid, getNginxPID())
            memRuns.add(getTotalMem(pid))
        self.assertEqual(len(memRuns), 1)
        killWebsocketSrv()

if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        killWebsocketSrv()
        pass

