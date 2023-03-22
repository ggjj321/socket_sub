# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
import json

import threading
from flask import Flask
from flask_socketio import SocketIO

import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String,
            "/transfrom_zed2_3dod_to_2d",
            self.listener_callback,
            1000)
        self.subscription  # prevent unused variable war

    def listener_callback(self, msg):
        self.get_logger().info('I heard: ' + msg.data)
        self.zed2_od_msg = msg.data
    
    def get_zed2_od_msg(self):
        return self.zed2_od_msg
    
class ZedSocket(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        socketio.run(app, host='127.0.0.1', port=2222)

class SocketHandle(threading.Thread):
    def __init__(self, get_zed2_od_msg):
        threading.Thread.__init__(self)
        self.get_zed2_od_msg = get_zed2_od_msg

    def run(self):
        self.send_zed_od_data()

    def send_zed_od_data(self):
        time.sleep(0.5)

        zed2_od_result_array = self.get_zed2_od_msg().split()

        # 2d: 33 7 label: Person label_id: 11
        # 0   1  2 3      4      5         6
        zed2_od_result_to_json = {
            'x' : int(zed2_od_result_array[1]),
            'y' : int(zed2_od_result_array[2]),
            'label' : zed2_od_result_array[4],
            'id' : int(zed2_od_result_array[6])
        }

        socketio.emit('zed2_od', json.dumps(zed2_od_result_to_json))            
        self.send_zed_od_data()

def main(args=None):
    rclpy.init(args=args) 
    minimal_subscriber = MinimalSubscriber()

    socketThread = ZedSocket()
    socketThread.start()

    socketHandle = SocketHandle(minimal_subscriber.get_zed2_od_msg)
    socketHandle.start()

    rclpy.spin(minimal_subscriber)

    # Destroy the nodeexplicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
