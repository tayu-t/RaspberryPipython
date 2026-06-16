# -*- coding: utf-8 -*-
# システムテストファイル
# TConnectの使用
import time
import pigpio
from ControlManager import ControlManager

# pigpioの初期化
pi = pigpio.pi()

connectManager = ControlManager(pi)

if __name__ == "__main__":
    
    try:
        while connectManager.update():
            time.sleep(0.01)  #  CPU使用率を下げるために少し待機 
            pass
            
    except KeyboardInterrupt:
        print("プログラムを終了します")
    finally:
        pi.stop()
