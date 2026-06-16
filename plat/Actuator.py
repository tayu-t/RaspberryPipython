#各種Actuatorが継承する基底クラス
"""
Actuatorの属性:
・name: Actuatorの名前
・param: Actuatorのパラメータ(pwmPinやdirPinなど)
・weight: Actuatorの重み
・response: Actuatorの応答関数の情報(typeやcoefficientなど)

Actuatorの関数:
・init: Actuatorの初期化関数。nameやparam、weight、responseなどを設定する
・update: 毎フレーム呼び出される関数。Actuatorの重みや応答関数に基づいて、ドライバーに指令を送る等
・getFeedbackList  : Actuatorのフィードバックを取得する関数。エンコーダーの値や現在の速度などを取得する
・stop: Actuatorを停止する関数
"""
import pigpio
from typing import Any

class Actuator:
    def __init__(self,pi, name: str, driver: str, param: dict, weight: dict[str, float], response: dict[str, Any]):
        self.name = name
        self.pi = pi
        self.driver = driver
        self.param = param
        self.weight = weight
        self.response = response
        if(response['type'] == "polynomial" or response['type'] == "linear"):
            self.coefficients = [float(x) for x in response['coefficient'].split(",")]
            self.response['type'] = "polynomial"
            
    def update(self,u):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def getFeedbackList(self)->list[list]:
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def stop(self):
        raise NotImplementedError("This method should be implemented by subclasses")
        
    