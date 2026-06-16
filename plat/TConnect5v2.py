"""
4との違い
・LCDManagerクラスの追加
・IntArrayで受け取るのではなくfloatArrayで受け取るように変更
"""

import socket
import struct
from enum import Enum
import time
import threading
import cv2
from LcdManager import LcdManager
import json
from pathlib import Path
from typing import List, Dict, Any

useLcd = False


class ServerState(Enum):
    NotConnected = 0
    Connected = 1

class ConnectManager:
    formatString = 'f' * 100
    receiveDataArray = [0] * 100  # Androidアプリ側からのデータを格納する配列
    sendDataArray = [0] * 12  # float型のデータを格納する配列
    
    state = ServerState.NotConnected  # 状態を初期化
    androidIP = ""
    jsonDataChangeFlag = False  # JSONデータが変更されたかどうかのフラグ
    
    sendFrame = None  # カメラのフレームを指定する変数
    
    def __init__(self,serverIP):
        self.state = ServerState.NotConnected
        self._serverInit(serverIP)  # サーバーの初期化を呼び出す
        print("サーバーの初期化完了")
        self._clientInit()  # クライアントの初期化を呼び出す
        print("クライアントの初期化完了")
        
        #LCD表示用のスレッドを開始
        if useLcd:
            
            LcdManager = LcdManager()
            self._ShowLcdThread = threading.Thread(target=self._ShowLcdThread, daemon = True)
            self._ShowLcdThread.start()
        
        self.lock = threading.Lock()
        
    def __del__(self):
        """クラスのインスタンスが削除されるときに呼ばれる"""
        if self.udpSocket:
            self.udpSocket.close()
        if self.tcpSocket:
            self.tcpSocket.close()
        if self.sendCameraSocket:
            self.sendCameraSocket.close()
        if self.sendDataSocket:
            self.sendDataSocket.close()
        print("ソケットを閉じました")

    def setSendFrame(self, frame):
        with self.lock:
            self.sendFrame = frame
    
    def _createReceiveThread(self):
        """スレッドを作成する"""
        self.receiveThread = threading.Thread(target=self._receiveDataThread, daemon=True)
    
    def _createCameraSendThread(self):
        """スレッドを作成する"""
        self.cameraThread = threading.Thread(target=self._sendCameraDataThread, daemon=True)
        
    def _createDataSendThread(self):
        """スレッドを作成する"""
        self.dataThread = threading.Thread(target=self._sendDataThread, daemon=True)
    
    def _serverInit(self, serverIP):
        self.serverIP = serverIP  # "
        self.serverPort = 49154  # 固定値
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
        self.udpSocket.bind((self.serverIP, self.serverPort))
        self.udpSocket.settimeout(5)  # タイムアウトを設定（5秒）
        
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.bind((self.serverIP, self.serverPort))  # TCPポートをバインド
        self.tcpSocket.listen(1)  # 接続を待機する
        
        self._createReceiveThread()  # 受信スレッドを作成
        
        
    def _clientInit(self):
        self.sendCameraSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sendCameraSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # 送信バッファサイズを設定
        self.sendCameraPort = 49155 # カメラ用ポート番号
        
        self.sendDataSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sendDataSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.sendDataPort = 49156 # 送信先ポート番号
        
        self._createCameraSendThread()  # カメラ送信スレッドを
        self._createDataSendThread()  # データ送信スレッドを作成
        for i in range(len(self.sendDataArray)):
            #送るデータを初期化
            self.sendDataArray[i] = 0
            
    def startReceiveThread(self):
        """受信スレッドを開始する"""
        if(self.receiveThread is not None and not self.receiveThread.is_alive()):
            self.receiveThread.start()
            print("受信スレッドを開始しました")
            
    def startCameraSendThread(self):
        """カメラ送信スレッドを開始する"""
        if(self.cameraThread is not None and not self.cameraThread.is_alive()):
            self.cameraThread.start()
            print("カメラ送信スレッドを開始しました")
    
    def startDataSendThread(self):
        """データ送信スレッドを開始する"""
        if(self.dataThread is not None and not self.dataThread.is_alive()):
            self.dataThread.start()
            print("データ送信スレッドを開始しました")
            
    def _sendDataThread(self):
        """データを送信する
        """
        while True:
            if(self.state == ServerState.NotConnected):
                break
            # 送信するデータをバイトデータに変換
            data = struct.pack('f'*12, *self.sendDataArray)
            
            # データを送信
            self.sendDataSocket.sendto(data, (self.androidIP,self.sendDataPort))
            
            # 適切な送信間隔を設定
            time.sleep(0.01)
    
    def getIPAddress(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 外部のDNSに接続を試みてIPを取得（実際に通信は発生しない）
            s.connect(('8.8.8.8', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
            
    
    def _ShowLcdThread(self):
        while True:
            if(useLcd == False):
                pass
            #終了してないか確認するために現在時刻を表示する
            self.LcdManager.lcd_string(time.strftime("%H:%M:%S"), self.LcdManager.LCD_LINE_1)
            
            self.LcdManager.lcd_string(self.getIPAddress(), self.LcdManager.LCD_LINE_2)
            if(self.state == ServerState.NotConnected):
                self.LcdManager.lcd_string("Not Connected", self.LcdManager.LCD_LINE_3)
            else:
                self.LcdManager.lcd_string("Connected", self.LcdManager.LCD_LINE_3)
            self.LcdManager.lcd_string(f"Vol: {self.sendDataArray[1]:.3f} V" ,self.LcdManager.LCD_LINE_4)
        
            #time.sleep(0.01)
            
    def _sendCameraDataThread(self):
        while True:
            if(self.state == ServerState.NotConnected):
                break
            
            canSend = False
            
            with self.lock:
                if(self.sendFrame is not None):
                    canSend = True

                    nowSendFrame = self.sendFrame
                    self.sendFrame = None  # 一度取り出したら空にする
        
            
            #nowSendFrame = self.sendFrame.copy()
            #nowSendFrame = self.sendFrame
            
            if(canSend == True):
                # フレームをリサイズ
                #nowSendFrame = cv2.resize(nowSendFrame, (640, 480))
            
                # フレームをJPEG形式にエンコード
                _, encodedFrame = cv2.imencode('.jpg', nowSendFrame, [cv2.IMWRITE_JPEG_QUALITY, 30])
                frameData = encodedFrame.tobytes()

                # データを一括送信
                self.sendCameraSocket.sendto(frameData, (self.androidIP,self.sendCameraPort))
                time.sleep(0.033)
            else:
                self.sendCameraSocket.sendto(b'', (self.androidIP,self.sendCameraPort))
    
    #receiveDataNum = 0
    
    def _receiveDataThread(self):
        """データを受信する
        """
        while(True):
            try:
                
                if(self.state == ServerState.Connected):
                    #受信したデータをバイトデータからfloat型の配列に変換
                    data, clientAddress = self.udpSocket.recvfrom(1024)
                    self.receiveDataArray = list(struct.unpack(self.formatString, data))
                    #print(f"Received data: {self.receiveDataArray}")
                    #self.receiveDataNum += 1
                   # print(f"Receive count: {self.receiveDataNum}")
                   # packetLossRate = (self.receiveDataNum) / self.receiveDataArray[0] * 100
                   # print(f"Packet loss rate: {packetLossRate:.2f}%")
                else:
                    self.state = ServerState.NotConnected
                    self._receiveTCPData()  # TCP接続を待機する
                    continue
            except socket.timeout:
                self.state = ServerState.NotConnected
                print("タイムアウト: データを受信できませんでした")
                continue
                
            except struct.error:
                print("receivedData Error")
                self.state = ServerState.NotConnected
                continue
    
    def _receiveTCPData(self):
        print("Waiting for TCP connection...")
        conn, clientAddress = self.tcpSocket.accept()  # クライアントからの接続を受け入れる
        print(f"TCP connection established with {clientAddress}")
        try:

            while True:
                receivedChucks = []
                fullData = b""
                conn.settimeout(0.1)  # タイムアウトを設定（5秒）
                getHeader = False
                while True:
                    try:
                        chunk = conn.recv(8192)  # データを受信
                    except socket.timeout:
                        print("TCP receive timeout")
                        try:
                            conn.sendall(b"1")
                        except OSError:
                            pass
                    print(f"Received TCP chunk: {chunk}")
                    if not chunk:
                        break  # クライアントが切断した場合
                    
                    print(f"Received TCP chunk: {chunk}")
                    receivedChucks.append(chunk)
                    
                    #現在まで届いた最後のデータの最後尾が\nである,
                    #もしくは最初がConnectであるかチェック
                    
                    if chunk == b"Connect":
                        fullData = chunk
                        break
                    
                    if chunk.endswith(b"\n"):
                     
                        
                        fullData = b"".join(receivedChucks)
                        break
                    
                    """
                    if b"JSON_UPDATE:" in chunk:
                        if not getHeader:
                            fullData = chunk
                            getHeader = True
                        else:
                            break
                    """

                if not fullData:
                    return
                
                data = fullData
                print(f"Received TCP data: {data}")
                if data == b"Connect":
                    print("Connected")
                    responseMessage = "Connected"
                    self.androidIP = clientAddress[0]
                    print(f"Client IP: {self.androidIP}")
                    conn.sendall(responseMessage.encode())
                    self.state = ServerState.Connected
                    self.waitSendThreadsFinish()#既存のスレッドがあれば終了を待つ
                    self.startCameraSendThread()
                    self.startDataSendThread()
                    break  # ← ここで内側のwhileを抜ける
                elif b"JSON_UPDATE:" in data:                    
                    print("Received JSON data change notification")
                    # 最後のJSON_UPDATE:を探して、そこから後ろを抽出
                    json_update_index = data.rfind(b"JSON_UPDATE:")
                    if json_update_index != -1:
                        json_str = data[json_update_index + len(b"JSON_UPDATE:"):].decode('utf-8')
                        print(f"Received JSON data: {json_str}")
                        try:
                            json_dict = json.loads(json_str)
                            save_path = Path(__file__).resolve().parent / 'test.json'
                            with open(save_path, 'w', encoding="utf-8-sig") as jsonFile:
                                json.dump(json_dict, jsonFile, ensure_ascii=False, indent=4)
                            # ファイル保存処理...
                            self.jsonDataChangeFlag = True
                            print("send receive1")
                            # クライアントに成功レスポンスを送信
                            conn.sendall(b"1")  # 成功レスポンス
                            print("send receive2")
                            conn.close()  # 接続を閉じる
                        except json.JSONDecodeError:
                            print("Invalid JSON format received")
                            conn.sendall(b"JSON_ERROR")        
                        except IOError as e:
                            # ファイル書き込み権限やディスクフルなどのエラー
                            print(f"File system error: {e}")
                            conn.sendall(b"STORAGE_ERROR")
                    
                    
                    self.jsonDataChangeFlag = True
                    break  # ← ここで内側のwhileを抜ける
                else:
                    print("Unknown TCP message received")
                    #conn.sendall(b"UNKNOWN_COMMAND")
                
        finally:
            conn.close()  # 接続を閉じる
    
    def waitSendThreadsFinish(self):
        """すべての送信スレッドが終了するのを待つ"""
        if hasattr(self, "cameraThread") and self.cameraThread.is_alive():
            self.cameraThread.join()
        if hasattr(self, "dataThread") and self.dataThread.is_alive():
            self.dataThread.join()
        print("All send threads have finished.")
        # スレッドを再作成
        self._createCameraSendThread()
        self._createDataSendThread()


class TConnect:  
   
    
    def __init__(self,serverIP = "0.0.0.0") :
        self.__connectManager = ConnectManager(serverIP) 
    
    def startReceiveThread(self):
        """データ受信スレッドを開始する"""
        try:
            self.__connectManager.startReceiveThread()
        except Exception as e:
            print(f"Error starting receive thread: {e}")
    
    def setSendFrame(self,frame):
        """カメラのフレームを設定する"""
        
        self.__connectManager.setSendFrame(frame)
    
    @property
    def ServerState(self):
        """サーバーの状態を取得する"""
        return self.__connectManager.state
    
    def startSendThread(self):
        """データ送信スレッドを開始する"""
        self.__connectManager.waitSendThreadsFinish()  # 既存のスレッドがあれば終了を待つ
        self.__connectManager.startCameraSendThread()
        self.__connectManager.startDataSendThread()
        
    @property
    def receiveDataArray(self):
        """受信したデータを取得する"""
        return self.__connectManager.receiveDataArray

    @property
    def SendDataArray(self):
        """送信するデータを取得する"""
        return self.__connectManager.sendDataArray
    
    def setSensor1Data(self,data):
        """センサー1のデータを設定する"""
        self.__connectManager.sendDataArray[0] = data
    def setSensor2Data(self,data):
        """センサー2のデータを設定する"""
        self.__connectManager.sendDataArray[1] = data   
    def setSensor3Data(self,data):
        """センサー3のデータを設定する"""
        self.__connectManager.sendDataArray[2] = data
    def setSensor4Data(self,data):
        """センサー4のデータを設定する"""
        self.__connectManager.sendDataArray[3] = data
        
    def setSensorData(self,index,data):
        self.__connectManager.sendDataArray[index - 1] = data
        
    def resetReceiveDataArray(self):
        """受信データ配列をリセットする"""
        for i in range(len(self.__connectManager.receiveDataArray)):
            self.__connectManager.receiveDataArray[i] = 0
            
    def getJSONDataChangeFlag(self):
        """JSONデータが変更されたかどうかのフラグを取得する"""
        return self.__connectManager.jsonDataChangeFlag
    
    def setJsonDataChangeFlag(self,flag):
        """JSONデータが変更されたかどうかのフラグを設定する"""
        self.__connectManager.jsonDataChangeFlag = flag



