"""
Sensorを管理するクラス
SensorManagerの属性:
・sensors: Sensorのリスト

SensorManagerの関数:
・init: SensorManagerの初期化関数。Sensorのリストを初期化する
・importModules: SensorのリストをJSONデータからインポートする関数。各Sensorのドライバーに応じて、対応するドライバーをセットする
・updateSensors: 毎フレーム呼び出される関数。別threadで実行される
・getFeedback: Sensorのフィードバックを取得する関数。エンコーダーの値や現在の速度などを取得する
"""
import importlib
from Sensor import Sensor
from TConnect5v2 import TConnect
from TConnect5v2 import ServerState
import pigpio
from typing import List, Dict, Any

class SensorManager:
    def __init__(self, pi: pigpio.pi, tConnect: TConnect, data: Dict[str, Any]):
        self.pi = pi
        self.tConnect = tConnect
        self.data = data
        self.sensors = []
        self.importModules()
        
    def importModules(self):
        #sensorsがnullでない限り、sensorのpluginに応じてモジュールをセットする
        if(self.data['sensor'] is None):
            print("No sensor data found in JSON")
            return
        for sensor in self.data['sensor']:
            pluginName = sensor['plugin']
            try:
                module = importlib.import_module(f"plugin.{pluginName}.{pluginName}")
            except ModuleNotFoundError:
                try:
                    module = importlib.import_module(f"plugin.{pluginName}")
                except ModuleNotFoundError:
                    raise ImportError(f"Module not found for plugin: {pluginName}")

            sensorClass = getattr(module, pluginName, None)
            
            if sensorClass is None:
                sensorClass = getattr(module, sensor['driver'], None)
            if sensorClass is None:
                raise ImportError(f"Sensor class not found in module '{pluginName}'. Expected '{pluginName}'.")

            sensor = sensorClass(self.pi, sensor['name'], sensor['driver'], sensor['param'])
            self.sensors.append(sensor)
            
    def updateSensors(self):
        for sensor in self.sensors:
            #print("here in sensorManager updateSensors")
            
            sensor.update(self.tConnect.receiveDataArray)
    
    def getFeedbackList(self)->list[list[list]]:
        feedback : list = []
        for sensor in self.sensors:
            feedback.append(sensor.getFeedbackList())
        
        return feedback