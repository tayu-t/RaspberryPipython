"""_summary_
制御信号 Pwm を出力するサーボモーターのクラス

テストサーボ
GWServo
S03T2BBMG

"""
from Actuator import Actuator
import pigpio
from typing import Any

class PWMServo(Actuator):
    def __init__(self,pi, name: str, driver: str, param: dict, weight: dict[str, float], response: dict[str, Any]):
        self.name = name
        self.pi = pi
        self.driver = driver
        self.param = param
        self.weight = weight
        self.response = response
        self.pwmPin : int = int(param['pwmPin'])
        self.returnDegIndex : int = int(param['degReturnIndex'])
        self.pwm = 0.0
        if(response['type'] == "polynomial" or response['type'] == "linear"):
            self.coefficients = [float(x) for x in response['coefficient'].split(",")]
            self.response['type'] = "polynomial"
            
        self.initPins()
    
    def initPins(self):
        """各ピンの初期化
        pwmPinのみしか使わないので、pwmPinのみ初期化する
        """
        self.pi.set_mode(self.pwmPin, pigpio.OUTPUT)    
    
    
    def update(self,u):
        # PWMサーボへの指令送信コードはここに追加
        tempU = 0.0
        self.pwm = 0.0
        # 重み付き和を計算
        for weight in self.weight:
            tempU += u[int(weight["index"])] * weight["weight"]
        
        #print(f"Calculated weighted input: {tempU}")
        
        # 応答関数に基づいて速度を計算
        if(self.response['type'] == "polynomial"):
            for i, coeff in enumerate(self.coefficients):
                self.pwm += coeff * (tempU ** (self.coefficients.__len__() - 1 - i))
        
        
        #print(f"Calculated PWM: {self.pwm}")
        
        self.pwm = self.pwm * (2500-500) + 500  # 0-1の値を500-2500の範囲に変換
        if(self.pwm < 500):
            self.pwm = 500
        elif(self.pwm > 2500):
            self.pwm = 2500
        
        #print(f"Converted PWM: {self.pwm}")
        self.pi.set_servo_pulsewidth(self.pwmPin, int(self.pwm))  # 中央
                    

    def getFeedbackList(self)-> list[list]:
        # エンコーダーの値や現在の速度などを取得するコードはここに追加
    
        if(1 <= self.returnDegIndex <= 4):
            deg = (self.pwm - 500) / (2500 - 500) * 180  # デューティ比から角度を計算（例: 0.5が0度、0.25が-90度、0.75が90度）
            
            return [[self.returnDegIndex, deg]]
        return []
        
    def stop(self):
        pass
    