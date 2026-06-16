"""
Actuatorを管理するクラス
ActuatorManagerの属性:
・actuators: Actuatorのリスト

ActuatorManagerの関数:
・init: ActuatorManagerの初期化関数。Actuatorのリストを初期化する
・importModules: ActuatorのリストをJSONデータからインポートする関数。各Actuatorのドライバーに応じて、対応するドライバーをセットする
・updateActuators: 毎フレーム呼び出される関数。別threadで実行される
・getFeedback: Actuatorのフィードバックを取得する関数。エンコーダーの値や現在の速度などを取得する
"""
import importlib
from Actuator import Actuator
from TConnect5v2 import TConnect
from TConnect5v2 import ServerState
import pigpio
from typing import List, Dict, Any

class ActuatorManager:
    def __init__(self, pi: pigpio.pi, tConnect: TConnect, data: Dict[str, Any]):
        self.pi = pi
        self.tConnect = tConnect
        self.data = data
        self.actuators = []
        self.importModules()
        
    def importModules(self):
        #actuatorsがnullでない限り、actuatorのpluginに応じてモジュールをセットする
        if(self.data['actuator'] is None):
            print("No actuator data found in JSON")
        else:
            for act in self.data['actuator']:
                pluginName = act['plugin']
                try:
                    module = importlib.import_module(f"plugin.{pluginName}.{pluginName}")
                except ModuleNotFoundError:
                    try:
                        module = importlib.import_module(f"plugin.{pluginName}")
                    except ModuleNotFoundError:
                        raise ImportError(f"Module not found for plugin: {pluginName}")

                # debug: show which module was loaded and its attributes
                try:
                    mod_name = getattr(module, "__name__", str(module))
                    mod_file = getattr(module, "__file__", None)
                    print(f"Loaded module: {mod_name} file={mod_file}")
                    print("module attrs:", [a for a in dir(module) if not a.startswith('_')])
                except Exception as _:
                    pass

                actuatorClass = getattr(module, pluginName, None)
                if actuatorClass is None:
                    actuatorClass = getattr(module, act['driver'], None)
                if actuatorClass is None:
                    raise ImportError(f"Actuator class not found in module '{pluginName}'. Expected '{pluginName}' or '{act['driver']}'.")


                actuator = actuatorClass(self.pi, act['name'], act['driver'], act['param'], act['weights'], act['response'])
                self.actuators.append(actuator)
        
        if(self.data['supervisorActuator'] is None):
            print("No supervisor actuator data found in JSON")
        else:
            for act in self.data['supervisorActuator']:
                pluginName = act['plugin']
                try:
                    module = importlib.import_module(f"plugin.{pluginName}.{pluginName}")
                except ModuleNotFoundError:
                    try:
                        module = importlib.import_module(f"plugin.{pluginName}")
                    except ModuleNotFoundError:
                        raise ImportError(f"Module not found for plugin: {pluginName}")

                # debug: show which module was loaded and its attributes for supervisorActuator
                try:
                    mod_name = getattr(module, "__name__", str(module))
                    mod_file = getattr(module, "__file__", None)
                    print(f"Loaded supervisor module: {mod_name} file={mod_file}")
                    print("supervisor module attrs:", [a for a in dir(module) if not a.startswith('_')])
                except Exception:
                    pass

                actuatorClass = getattr(module, pluginName, None)
                if actuatorClass is None:
                    actuatorClass = getattr(module, act['driver'], None)
                if actuatorClass is None:
                    raise ImportError(f"Actuator class not found in module '{pluginName}'. Expected '{pluginName}' or '{act['driver']}'.")


                actuator = actuatorClass(self.pi, act['name'], act['driver'], act['param'],act["subActuator"])
                self.actuators.append(actuator)
            
    def updateActuators(self):
        for actuator in self.actuators:
            actuator.update(self.tConnect.receiveDataArray)
    
    def getFeedbackList(self)->list[list[list]]:
        feedback : list = []
        for actuator in self.actuators:
            feedback.append(actuator.getFeedbackList())
        
        return feedback