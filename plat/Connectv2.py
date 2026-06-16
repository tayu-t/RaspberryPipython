# -*- coding: utf-8 -*-
# システムテストファイル
# TConnectの使用

#ControlManagerを使わないバージョン

import pigpio
from ActuatorManger import ActuatorManager
from TConnect5v2 import TConnect
from TConnect5v2 import ServerState
import pigpio
from pathlib import Path
import json
from picamera2 import Picamera2
import threading
import time

# pigpioの初期化
pi = pigpio.pi()


piCam = None
# カメラの初期設定（グレースケール、速度調整）
piCam = Picamera2()
piCam_config = piCam.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"},
    buffer_count = 1
)
piCam.configure(piCam_config)
piCam.start()
tConnect = TConnect()
actuatorManager = None
killUpdateActuators = threading.Event()
killUpdateSensors = threading.Event()
killCameraSend = threading.Event()
firstConnectCheck = False
firstNotConnectCheck = False
actuatorManager = None
senssorrManager = None
updateActuatorsThread = None
updateSensorsThread = None
cameraSendThread = None


def updateActuators(actuatorManager:ActuatorManager, killEvent):
    while not killEvent.is_set():
        if(actuatorManager is not None):
            actuatorManager.updateActuators()
        
            #フィードバックの取得
            feedback = actuatorManager.getFeedbackList()
            #tconnectにフィードバックを送る
            for fb in feedback:
                if(fb is not None):
                    if(len(fb) == 2):
                        tConnect.setSensorData(fb[0], fb[1])
        time.sleep(0.02)  # 50Hzで更新
    
        

def updateSensors(sensorsManager, killEvent):
    while not killEvent.is_set():
        if(sensorsManager is not None):
            sensorsManager.updateSensors()
        else:
            pass
        time.sleep(0.02)  # 50Hzで更新
        pass
        
        

def cameraSend(killEvent):
    while not killEvent.is_set():
        t0 = time.time()
        sendSet = (piCam.capture_array())
        t1 = time.time()
        tConnect.setSendFrame(sendSet)
        t2 = time.time()
        print(f"Capture: {(t1-t0)*1000:.1f}ms, SetFrame: {(t2-t1)*1000:.1f}ms")
        killEvent.wait(0.033)


def startAllThreads():
    global updateActuatorsThread, updateSensorsThread, cameraSendThread
    global killUpdateActuators,killUpdateSensors,killCameraSend
    killUpdateActuators.clear()
    killUpdateSensors.clear()
    killCameraSend.clear()
    updateActuatorsThread = threading.Thread(target=updateActuators, args=(actuatorManager, killUpdateActuators), daemon=True)
    updateSensorsThread = threading.Thread(target=updateSensors, args=(senssorrManager, killUpdateSensors), daemon=True)
    cameraSendThread = threading.Thread(target=cameraSend, args=(killCameraSend,), daemon=True)

    updateActuatorsThread.start()
    updateSensorsThread.start()
    cameraSendThread.start()
    
def stopAllThreads():
    global updateActuatorsThread, updateSensorsThread, cameraSendThread
    global killUpdateActuators,killUpdateSensors,killCameraSend
    killUpdateActuators.set()
    killUpdateSensors.set()
    killCameraSend.set()
    
    updateActuatorsThread.join()
    updateSensorsThread.join()
    cameraSendThread.join()
    
    # スレッド終了後、イベントをクリア
    killUpdateActuators.clear()
    killUpdateSensors.clear()
    killCameraSend.clear()
      
def readJSONData():
    global actuatorManager
    stopAllThreads()
    json_path = Path(__file__).resolve().parent / 'test.json'
    with open(json_path, encoding="utf-8-sig") as jsonFile:
        data = json.load(jsonFile)
    actuatorManager = ActuatorManager(pi, tConnect, data)
    jsonFile.close()


def updateServerConnected():
    global firstConnectCheck 
    if not firstConnectCheck:
        startAllThreads()
        print("Server Connected")
        firstConnectCheck = True
        firstNotConnectCheck = False

def updateServerNotConnected():
    global firstNotConnectCheck
    if not firstNotConnectCheck:
        stopAllThreads()
        print("Server Not Connected")
        firstNotConnectCheck = True
        firstConnectCheck = False

if __name__ == "__main__":
    startAllThreads()
    readJSONData()
    tConnect.startReceiveThread()
    try:
        while True:
            if tConnect.ServerState == ServerState.Connected:
                updateServerConnected()
            else:
                updateServerNotConnected()
            time.sleep(0.01)

            
    except KeyboardInterrupt:
        print("プログラムを終了します")
    finally:
        stopAllThreads()
        pi.stop()
