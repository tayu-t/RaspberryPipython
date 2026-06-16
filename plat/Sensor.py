"""
Sensorモジュール用の基底クラス
引数
self,pi, name: str, driver: str, param: dict
name: センサの名前
driver: センサのドライバーの種類
param: センサのパラメータ(pwmPinやdirPin,応答のインデックスなど
関数
init: センサの初期化関数。nameやparamなどを設定する
update: 毎フレーム呼び出される関数。センサの値を更新する
getFeedbackList  : センサのフィードバックを取得する関数。センサの値をリストで返す
"""

import pigpio
from typing import Any

class Sensor:
    def __init__(self,pi, name: str, driver: str, param: dict):
        self.name = name
        self.pi = pi
        self.driver = driver
        self.param = param
            
    def update(self,u):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def getFeedbackList(self)->list[list]:
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def stop(self):
        raise NotImplementedError("This method should be implemented by subclasses")
        
    