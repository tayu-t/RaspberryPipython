"""
PCA9685のためのプラグイン
サーボコントローラ
ActuatorType : SupervisorActuator
"""

from Actuator import Actuator
import busio
import board
import pigpio
from typing import Any
from adafruit_pca9685 import PCA9685 



class SubServo:
    def __init__(self, param: dict, weight: dict[str, float], response: dict[str, Any]):
        self.id = int(param['ID'])
        self.returnDegIndex = int(param['returnDegIndex'])
        self.maxPulse = param['maxPulse']
        self.minPulse = param['minPulse']
        self.minDegree = param['minDegree']
        self.maxDegree = param['maxDegree']
        self.weight = weight
        self.response = response
        self.currentDeg = 0.0
        self.pulse = 0.0
        
    def calcResoponse(self, u):
        tempU = 0.0
        # 重み付き和を計算
        for weight in self.weight:
            tempU += u[int(weight["index"])] * weight["weight"]
        
        #print(f"Calculated weighted input: {tempU}")
        
        # 応答関数に基づいて速度を計算
        if(self.response['type'] == "polynomial"):
            pwm = 0.0
            coefficients = [float(x) for x in self.response['coefficient'].split(",")]
            for i, coeff in enumerate(coefficients):
                pwm += coeff * (tempU ** (coefficients.__len__() - 1 - i))
            return pwm
        
        
        
        return tempU
    
    def getFeedback(self):
        self.currentDeg = (self.pulse - self.minPulse) * (self.maxDegree - self.minDegree) / (self.maxPulse - self.minPulse) + self.minDegree
        return [self.returnDegIndex,self.currentDeg]
    
    

class PCA9685Controller(Actuator):
    SET_FREQ = 50  # サーボモーターの周波数（Hz）
    stepMax = 65535  # PCA9685の最大ステップ数
    subActuators : list[SubServo] = []
    
    
    def __init__(self,pi, name: str, driver: str, param: dict,subActuator: Any):
        self.name = name
        self.pi = pi
        self.driver = driver
        self.param = param
        self.subActuator = subActuator        
        self.initSubActuator()
        
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c)
        self.pca.frequency = self.SET_FREQ
        

    def __del__(self):
        for sub in self.subActuators:
            self.pca.channels[sub.id].duty_cycle = 0  # サーボを停止
        
        self.pca.deinit()
        pass

    def initSubActuator(self):
        """各ピンの初期化
        pwmPinのみしか使わないので、pwmPinのみ初期化する
        """
        
        for sub in self.subActuator:
            actuator = SubServo(sub['param'], sub['weights'], sub['response'])
            self.subActuators.append(actuator)
    
    def update(self,u):
        # PWMサーボへの指令送信コードはここに追加
        tempU = 0.0
        for sub in self.subActuators:
            tempU = sub.calcResoponse(u)
            
            centerPulse = (sub.maxPulse + sub.minPulse) / 2.0
            pulse = tempU * (sub.maxPulse - sub.minPulse) / 2 + centerPulse
            sub.pulse = pulse
            duty_cycle = (pulse / (1000.0 / self.SET_FREQ)) * self.stepMax
            self.pca.channels[int(sub.id)].duty_cycle = int(duty_cycle)
            
    
    

    def getFeedbackList(self)-> list[list]:
        list = []
        for sub in self.subActuators:
            list.append(sub.getFeedback())
        return list
        
    def stop(self):
        pass
    