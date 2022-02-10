import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import threading
import time
import numpy as np
import pandas as pd
import keyboard
from std_msgs.msg import Float32

class Handle_reader(Node):
    def __init__(self):
        super().__init__("handle_reader")
        self.start_sign = False

        self.handle_sub = self.create_subscription(Joy, "/G29/joy", self.joy_callback, 1)
        self.time_pub = self.create_publisher(Float32, "experiment_time")
        self.driving_list = []
        self.handle_deg = -999
        self.accel = -999
        self.breake = -999
        self.start_sign = False
        self.start_button = 0
        self.finish_button = 0
        self.record_sec = 0
        self.start_time = time.time()
        self.time = Float32()

        # parameter
        self.recording_rate = 0.01

        keyboard_threading = threading.Thread(target = self.thread_keyboard)
        keyboard_threading.start()
        record_threading = threading.Thread(target = self.driving_recoder_threading)
        record_threading.start()

    def joy_callback(self, msg):
        # print("get_joy con")
        self.handle_deg = msg.axes[0] * 450 # G29は両側450度
        self.accel = (msg.axes[2] + 1) / 2
        self.breake = (msg.axes[3] + 1) / 2
        self.start_button = msg.buttons[6]
        self.finish_button = msg.buttons[7]
        # print("self.handle_deg : ", self.handle_deg)
    
    def thread_keyboard(self):
        while True:
            keyreturn = input()
            # print("get_start_stop")
            if (keyreturn == "") and (self.start_sign == False):
                print("Start !!!!")
                self.start_sign = True
                self.record_sec = self.recording_rate
                self.handle_deg = -999
                self.accel = -999
                self.breake = -999

                # 記録時間の計測
                self.start_time = time.time()
            elif (keyreturn == "f") and (self.start_sign == True):
                self.start_sign = False

                # csvの出力
                self.driving_array = np.array(self.driving_list)
                print("driving_array : \n", self.driving_array)
                dict = {"time[s]":self.driving_array[:, 0], "handle[deg]":self.driving_array[:, 1], "accel[0-1]":self.driving_array[:, 2], "breake[0-1]":self.driving_array[:, 3], "marker":self.driving_array[:, 4]}
                df = pd.DataFrame(dict)
                df = df.replace(-999, "null")
                print("DF :\n", df)
                df.to_csv("result.csv")

                # 記録時間の計測終了
                self.finish_time = time.time() - self.start_time
                print("Stop !!!")
                self.driving_list = []
            else:
                continue

        # time.sleep(0.5)
    
    def driving_recoder_threading(self):
        while True:
            self.mid_time = round(time.time() - self.start_time, len(str(int(1 / self.recording_rate))) - 1)
            # print("self.recording_rate : ", str(int(1 / self.recording_rate)))
            # print("self.mid_time ", self.mid_time)
            #print("self.mid_time ", round(self.mid_time, 1))
            # print("self.start_sign : ", self.start_sign)
            if (self.start_sign == True):
                print("self.mid_time ", self.mid_time)
                self.time.data = self.mid_time
                self.time_pub.publish(self.time)
                # if keyboard.read_key() == "m": # mが押されたらマーカーを押す
                #     self.driving_list.append([self.mid_time, self.handle_deg, self.accel, self.breake, 1])
                # else:
                #     self.driving_list.append([self.mid_time, self.handle_deg, self.accel, self.breake, 0])
                self.driving_list.append([self.mid_time, self.handle_deg, self.accel, self.breake, 0])
                time.sleep(0.01)
                
                

def main(args=None):
    rclpy.init(args=args)
    listener = Handle_reader()
    while True:
        rclpy.spin(listener)


if __name__ == "__main__":
    main()
    
