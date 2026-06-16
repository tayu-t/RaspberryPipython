"""
ControlManagerの役割
・ActuatorManagerとSensorManagerを管理する
・ActuatorManagerとSensorManagerの更新を行う
・ActuatorManagerとSensorManagerのフィードバックを取得する
・CameraThread,updateActuatorsThread,updateSensorsThreadなどのスレッド管理を行う
"""

from ActuatorManger import ActuatorManager
from SensorManager import SensorManager
from TConnect5v2 import TConnect
from TConnect5v2 import ServerState
import pigpio
from pathlib import Path
import json
from typing import List, Dict, Any
from picamera2 import Picamera2
import threading
import time

class ControlManager:
    def __init__(self,pi):
        
        self.pi = pi
        self.piCam = None
        self.tConnect = TConnect()
        self.actuatorManager = None
        self.sensorManager = None
        self.killUpdateActuators = threading.Event()
        self.killUpdateSensors = threading.Event()
        self.killCameraSend = threading.Event()
        self.firstConnectCheck = False
        self.firstNotConnectCheck = False
        self.updateControlManager = True

        time.sleep(1)  #初期化待ち socketがないといわれることがあるため、少し待機する
        self.setPiCam()
        self.startAllThreads()
        self.readJSONData()
        self.tConnect.startReceiveThread()
        

    def __del__(self):
        self.stopAllThreads()

    
    def setPiCam(self):
        #カメラの初期設定（グレースケール、速度調整）
        self.piCam = Picamera2()
        self.piCam_config = self.piCam.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            buffer_count = 1
        )
        self.piCam.configure(self.piCam_config)
        self.piCam.start()

    def readJSONData(self):
        
        json_path = Path(__file__).resolve().parent / 'test.json'
        with open(json_path, encoding="utf-8-sig") as jsonFile:
            data = json.load(jsonFile)
        self.actuatorManager = ActuatorManager(self.pi, self.tConnect, data)
        self.sensorManager = SensorManager(self.pi, self.tConnect, data)
        jsonFile.close()

    def update(self) -> bool:
        if self.tConnect.ServerState == ServerState.Connected:
            self.updateServerConnected()
        else:
            self.updateServerNotConnected()
        return self.updateControlManager
    

    def updateServerConnected(self):
        if self.firstConnectCheck == False:    
            self.startAllThreads()
            self.firstConnectCheck = True
            self.firstNotConnectCheck = False
        return
    
    def updateServerNotConnected(self):
        if self.firstNotConnectCheck == False:
            self.stopAllThreads()
            self.firstNotConnectCheck = True
            self.firstConnectCheck = False
        
        if(self.tConnect.getJSONDataChangeFlag()):
            self.readJSONData()
            self.tConnect.setJsonDataChangeFlag(False)
        
        
        return
    
    def updateActuators(self, killEvent):
        while not killEvent.is_set():
            if(self.actuatorManager is not None):
                self.actuatorManager.updateActuators()
            
                #フィードバックの取得
                feedback = self.actuatorManager.getFeedbackList()
                #tconnectにフィードバックを送る
                for fblist in feedback:
                    for fb in fblist:
                        if(fb is not None):
                            self.tConnect.setSensorData(fb[0], fb[1])
            time.sleep(0.02)  # 50Hzで更新
            
    
    def updateSensors(self, killEvent):
        while not killEvent.is_set():
            if(self.sensorManager is not None):
                self.sensorManager.updateSensors()
            
                #フィードバックの取得
                feedback = self.sensorManager.getFeedbackList()
                #tconnectにフィードバックを送る
                for fblist in feedback:
                    for fb in fblist:
                        if(fb is not None):
                            self.tConnect.setSensorData(fb[0], fb[1])
            time.sleep(0.02)  # 50Hzで更新
        
    
    def cameraSend(self, killEvent):
        while not killEvent.is_set():
            t0 = time.time()
            sendSet = (self.piCam.capture_array())
            t1 = time.time()
            self.tConnect.setSendFrame(sendSet)
            t2 = time.time()
            #print(f"Capture: {(t1-t0)*1000:.1f}ms, SetFrame: {(t2-t1)*1000:.1f}ms")
    
    def startAllThreads(self):
        self.updateActuatorsThread = threading.Thread(target=self.updateActuators, args=(self.killUpdateActuators,), daemon=True)
        self.updateSensorsThread = threading.Thread(target=self.updateSensors, args=(self.killUpdateSensors,), daemon=True)
        self.cameraSendThread = threading.Thread(target=self.cameraSend, args=(self.killCameraSend,), daemon=True)
        
        self.updateActuatorsThread.start()
        self.updateSensorsThread.start()
        self.cameraSendThread.start()
    
    def stopAllThreads(self):
        self.killUpdateActuators.set()
        self.killUpdateSensors.set()
        self.killCameraSend.set()
        
        self.updateActuatorsThread.join()
        self.updateSensorsThread.join()
        self.cameraSendThread.join()
        
        # スレッド終了後、イベントをクリア
        self.killUpdateActuators.clear()
        self.killUpdateSensors.clear()
        self.killCameraSend.clear()