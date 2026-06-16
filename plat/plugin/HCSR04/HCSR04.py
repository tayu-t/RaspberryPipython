"""
HC-SR04超音波センサ用のクラス
メンバ変数:
- trigPin: トリガーピンのGPIO番号
- echoPin: エコーピンのGPIO番号
- controlSensorIndex : sensorを使用するかどうか操作指令から決定するための変数(未使用 = -1)
- risingTime: 上昇エッジの時間
- lastState: 前回のエコーピンの状態
- speedOfSound: 音速（m/s） 
- cm: 測定された距離（cm）
- lastTrigTime: 最後にトリガーを送信した時間
- TrigSleepTime: トリガーを送信する間隔（秒）
- returnIndex: 測定値を返すためのインデックス
"""
import pigpio
import time
from Sensor import Sensor

class HCSR04(Sensor):
    trigPin = 15
    echoPin = 14
    risingTime = 0.0
    lastState : int = 0
    speedOfSound = 340.0
    cm : float = 0.0
    lastTrigTime = 0.0
    TrigSleepTime = 0.1 # トリガーを送信する間隔（秒）
    def __init__(self,pi, name: str, driver: str, param: dict):
        super().__init__(pi, name, driver, param)
        self.pi = pi
        self.trigPin = int(param['trigPin'])
        self.echoPin = int(param['echoPin'])
        self.controlSensorIndex = int(param['controlSensorIndex'])
        self.returnIndex = int(param['returnIndex'])
        self.initPins()
        
        print(f"Initialized HCSR04: trigPin={self.trigPin}, echoPin={self.echoPin}, controlSensorIndex={self.controlSensorIndex}, returnIndex={self.returnIndex}")
        
    
    def initPins(self):
        """各ピンの初期化
        """
        self.pi.set_mode(self.trigPin, pigpio.OUTPUT)
        self.pi.set_mode(self.echoPin, pigpio.INPUT)   
        
        #コールバックの設定
        self.pi.callback(self.echoPin,pigpio.EITHER_EDGE,self.echoCallback)
       
    def update(self,u):
        if(self.controlSensorIndex == -1 or u[self.controlSensorIndex] > 0):
            self.setTrig()
        else:
            self.cm = 0.0
            
    def setTrig(self):
        if(time.time() - self.lastTrigTime > self.TrigSleepTime):
            self.pi.write(self.trigPin, 0)
            time.sleep(0.002)  # 2ミリ秒の待機
            self.pi.write(self.trigPin, 1)
            time.sleep(0.00001)  # 10マイクロ秒のパルス
            self.pi.write(self.trigPin, 0)
            self.lastTrigTime = time.time()
        
        
    def echoCallback(self, gpio, level, tick):
        if level == 1:  # 上昇エッジ
            self.risingTime = tick
        elif level == 0 and self.risingTime != 0:  # 下降エッジ
            pulseDuration = pigpio.tickDiff(self.risingTime, tick) / 1e6  # 秒に変換
            self.cm = (pulseDuration * self.speedOfSound) / 2 * 100  # 距離をcmに変換
            self.risingTime = 0.0
            
    def getFeedbackList(self)->list[list]:
        return [[self.returnIndex,self.cm]]
   

