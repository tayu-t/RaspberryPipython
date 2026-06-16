"""
pololuのモータドライバを制御するためのクラス
エンコーダー読み取りあり
"""


import time
import pigpio
from typing import Any,List
from Actuator import Actuator

class PololuPwmDriver(Actuator):    
    
    def __init__(self, pi, name: str, driver: str, param: dict, weight: dict[str, float], response: dict[str, Any]):
        super().__init__(pi, name, driver, param, weight, response)
        # Pololu PWMドライバーの初期化コードはここに追加
        self.pi = pi
        
        self.pwmPin : int = int(param['pwmPin'])
        self.dirPin : int = int(param['dirPin'])
        self.encoderPinA : int = int(param['encoderPinA'])
        self.encoderPinB : int = int(param['encoderPinB'])
        self.cpr : int = int(param['cpr'])
        self.ppr : int = self.cpr // 4
        self.gearRatio : float = float(param['gearRatio'])
        self.rpm : float = 0
        self.position : int = 0
        self.preTime : float = time.time()
        self.useEncoder : bool = True if self.encoderPinA != -1 and self.encoderPinB != -1 else False
        self.rpmSensorIndex : int = int(param['rpmSensorIndex'])
        self.weights = weight
        self.response = response
        
        self.encoderCount : int = 0
        self.lastEncoderCount : int = 0
        
        print(f"Initialized PololuPwmDriver: pwmPin={self.pwmPin}, dirPin={self.dirPin}, encoderPinA={self.encoderPinA}, encoderPinB={self.encoderPinB}, cpr={self.cpr}, gearRatio={self.gearRatio}, rpmSensorIndex={self.rpmSensorIndex}")
        
        self.initPins()
    
        
    def initPins(self):
        """各ピンの初期化
        pwmPinとdirPinのみしか使わない場合があるので
        """
        self.pi.set_mode(self.pwmPin, pigpio.OUTPUT)
        self.pi.set_mode(self.dirPin, pigpio.OUTPUT)
        if self.useEncoder:
            self.pi.set_mode(self.encoderPinA, pigpio.INPUT)
            self.pi.set_mode(self.encoderPinB, pigpio.INPUT)
            self.pi.callback(self.encoderPinA, pigpio.RISING_EDGE, self.encoderCallback)
        
        

    def update(self, u):
        # Pololu PWMドライバーへの指令送信コードはここに追加
        #u: 操作指令の配列
        speed = 0.0
        tempU = 0.0
        
        # 重み付き和を計算
        for weight in self.weights:
            tempU += u[int(weight["index"])] * weight["weight"]
        
        # 応答関数に基づいて速度を計算
        if(self.response['type'] == "polynomial"):
            for i, coeff in enumerate(self.coefficients):
                speed += coeff * (tempU ** (self.coefficients.__len__() - 1 - i))
            if(speed > self.response['max']):
                speed = self.response['max']
            elif(speed < self.response['min']):
                speed = self.response['min']
            if(speed > self.response['maxThreshold']):
                speed = self.response['max']
            elif(speed < self.response['minThreshold']):
                speed = self.response['min']
        
        # 計算された速度に基づいてPWMと方向を設定
        self.setSpeed(abs(speed), speed < 0)
        
    def setPWM(self,pwm):
        """PWMの設定
        Args:
        pwm (int): PWMの値
        """
        pwm = max(min(pwm,255),0)
        self.pi.set_PWM_dutycycle(self.pwmPin, pwm)
        
    def setDirection(self,direction):
        self.pi.write(self.dirPin, direction)
        
    def setSpeed(self, pwm, direction):
        self.setPWM(pwm)
        self.setDirection(direction)
    
    
    def encoderCallback(self, gpio, level, tick):
        """エンコーダーのコールバック関数
        """
        self.encoderISR()
            
    def encoderISR(self):
        """エンコーダーの割り込み処理
        """
        if not self.useEncoder:
            return

        stateA = self.pi.read(self.encoderPinA)
        stateB = self.pi.read(self.encoderPinB)
        if stateA:
            if stateB:
                self.encoderCount += 1
            else:
                self.encoderCount -= 1
    
    def getFeedbackList(self)-> list[list]:
        # エンコーダーの値や現在の速度などを取得するコードはここに追加
        if self.useEncoder:
            self.calcRPM()
            if(1 <= self.rpmSensorIndex <= 4):
                return [[self.rpmSensorIndex, self.rpm]]
        return []
        
    
    def calcRPM(self):
        """RPMの計算
        """
        if (not self.useEncoder) or self.ppr == 0 or self.gearRatio == 0:
            self.rpm = 0
            return
        
        deltaPos = self.encoderCount - self.lastEncoderCount
        now = time.time()
        deltaTime = now - self.preTime
        if deltaTime <= 1:  # 時間差が非常に小さい場合はRPMを計算せずに返す,前回の値をそのまま使用する  
            return

        # 出力軸RPM: (回転数/秒) * 60 をギア比で割る
        self.rpm = (deltaPos / self.ppr) * 60 / deltaTime / self.gearRatio
        self.lastEncoderCount = self.encoderCount
        self.preTime = now
        
    
    def stop(self):
        # Actuatorを停止するコードはここに追加
        pass
