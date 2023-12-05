import sys
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt, QThread
from PyQt5.QtGui import QImage, QPixmap,  QStandardItemModel, QStandardItem
from PyQt5.uic import loadUi
import pyzbar.pyzbar as pyzbar
from playsound import playsound
import time
import pymysql
import subprocess
import os
# import sqlite3
# 커스텀 코드 임포트
from BoxDamageDetect.detect import *
# 

#patrol 임포트
import rospy
import actionlib
import time, signal, sys
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal

code = 'None'

#화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow) :
    def __init__(self) :
        super().__init__()
        loadUi("main5.ui", self)
        rospy.init_node('my_patrol')
        # QWidget.showFullScreen(self) # 전체화면
        self.cap = cv2.VideoCapture(0)
        # self.cap = cv2.VideoCapture("http://192.168.123.16:4747/video")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        self.btn_Camera.clicked.connect(self.search)
        self.btn_Inspection.clicked.connect(self.inspect)
        self.btn_Send.clicked.connect(self.transfer)
        self.Database_id.clicked.connect(self.call_test1)
        self.btn_comeback.clicked.connect(self.comeback)

        self.patrol_thread = Patrol(self.cap, self)
        self.comback_thread = ComeBack()
        self.abnormal_result = 0 
        self.patrol_thread.finished.connect(self.on_patrol_finished)

    
    def update(self): # 영상전송
        global code
        _, self.frame = self.cap.read()
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

        # 바코드 검출
        ####################
        barcodes = pyzbar.decode(self.frame)

        for barcode in barcodes:
            x, y, w, h = barcode.rect
            cv2.rectangle(self.frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            code = barcode.data.decode('utf-8')
        ####################

        height, width, channel = self.frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.pixmap = QPixmap.fromImage(q_image)
        self.LeftFrame.setPixmap(self.pixmap)
    
    def search(self): # [촬영] (수정본)
        self.textEdit.setStyleSheet("color: #000000;" "background-color: #00FF00;" "font: 30pt")
        self.textEdit.setText("촬영 시작")
        self.patrol_thread.start()  # Patrol 스레드 시작

    def on_patrol_finished(self):
        # patrol_thread의 작업이 완료된 후에 abnormal_result를 확인
        if self.patrol_thread.abnormal != 0:
            self.textEdit.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
            self.textEdit.setText("손상 의심")
            playsound("wrong.mp3")
        else:
            self.textEdit.setStyleSheet("color: #000000;" "background-color: #00FF00;" "font: 30pt")
            self.textEdit.setText("이상 없음")

    def inspect(self): # [검수]
        global code

        code_temp = code + ' '
        code_lite = code_temp[-5:-1]

        # Connect to the MariaDB database
        conn = pymysql.connect(
            user="ubuntu",
            password="1q2w3e4r",
            host="192.168.0.70",
            port=3306,
            database="brand"
        )
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM type WHERE ID = %s;', (code,))
        result = cursor.fetchone()

        print("Result:", result)

        if code == 'None':
            self.textEdit.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
            self.textEdit.setText("검출불가")
            self.codeInfo.setText("")
            self.brandInfo.setText("")
            playsound("wrong.mp3")
            code = 'None'


        elif result is None:
            self.brandInfo.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
            self.textEdit.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
            self.brandInfo.setText("검출불가")   
            self.textEdit.setText("검출불가")
            self.codeInfo.setText("")
            playsound("wrong.mp3")
            code = 'None'
        else:
            print(code)
            self.codeInfo.setStyleSheet("color: #FFFFFF;" "background-color: #8080FF;" "font: 30pt")
            self.textEdit.setStyleSheet("color: #FFFFFF;" "background-color: #8080FF;" "font: 30pt") 
            self.textEdit.setText('')   
            self.codeInfo.setText(code_lite)
            brand_info = ', '.join(str(item) for item in result[1:2])
            self.brandInfo.setStyleSheet("color: #FFFFFF;" "background-color: #8080FF;" "font: 30pt")
           # self.brandInfo.setText(f"{result[1:2]}")
            self.brandInfo.setText(brand_info)
            code = 'None'
    

    def transfer(self): # [전송]
        subprocess.call(["rm", "-rf", "/home/share/*"])
        subprocess.call(["cp", "-r", "/home/ubuntu/bot/BoxDamageDetect/runs/detect/", "/home/share"])
        self.textEdit.setStyleSheet("color: #000000;" "background-color: #00FF00;" "font: 30pt")
        self.textEdit.setText("전송 완료")

    def call_test1(self):   #데이터베이스 조회 (상품정보 클릭)
        try:
            subprocess.run(["python3", "databasereal.py"])
        except Exception as e:
            print(f"Error: {e}")
    
    # def comeback(self): # [복귀]
    #     self.comback_thread.start()

    def comeback(self, button_label): # [복귀]
        try:
            subprocess.run(["python3", "map.py"])
        except Exception as e:
            print(f"Error: {e}")
            self.textEdit.setText("")


class Patrol(QThread):

    # waypoints = [  # <1> 
    #     [(1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)],  #좌표, 바라보는 방향
    #     [(2.0, 0.0, 0.0), (0.0, 0.0, -0.7, 0.7)],
    #     [(3.0, 0.0, 0.0), (0.0, 0.0, -1.0, 0.0)],
    #     [(4.0, 0.0, 0.0), (0.0, 0.0, 0.7, 0.7)],
    #     [(0.5, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)]
    # ]

    # #원점 (15.4, -4.5, 0.0), (0.0, 0.0, -0.7, 0.7)
    # waypoints = [  # <1>  #(세로, 가로, 0) , (방향)
    #     [(15.5, -5.0, 0.0), (0.0, 0.0, -0.7, 0.7)],  #좌표, 바라보는 방향 (우)
    #     [(14.5, -6.0, 0.0), (0.0, 0.0, 0.0, 1.0)], #(상)
    #     [(15.0, -7.0, 0.0), (0.0, 0.0, 0.7, 0.7)], #(좌)
    #     [(17.0, -6.0, 0.0), (0.0, 0.0, 1.0, 0.0)],  #(하)
    #     [(15.5, -5.0, 0.0), (0.0, 0.0, -0.7, 0.7)]
    # ]

    #원점 (15.4, -4.5, 0.0), (0.0, 0.0, -0.7, 0.7)
    waypoints = [  # <1>  #(세로, 가로, 0) , (방향)
        [(13.415, -5.186, 0.0), (0.0, 0.0, -0.361, 0.932)],
        [(17.182, -5.613, 0.0), (0.0, 0.0, 0.972, -0.234)],
        [(17.136, -9.036, 0.0), (0.0, 0.0, 0.916, 0.399)],
        [(13.570, -8.771, 0.0), (0.0, 0.0, 0.304, 0.952)],
        [(15.498, -7.280, 0.0), (0.0, 0.0, 0.202, 0.965)],
        [(15.498, -7.264, 0.0), (0.0, 0.0, -0.317, 0.948)],
        [(15.498, -7.264, 0.0), (0.0, 0.0, 0.917, -0.396)],
        [(15.498, -7.264, 0.0), (0.0, 0.0, 0.930, 0.366)], 
    ]

    def __init__(self, cap, window_class):
        super().__init__()
        self.cap = cap
        self.window_class = window_class
        _, self.frame = self.cap.read()
        self.RGBframe = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        # rospy.init_node('my_patrol')
        self.count = 0
        self.abnormal = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.clear_global_costmap)

    def run(self):
        move_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        move_client.wait_for_server()
        
        save_path = "./BoxDamageDetect/test"
        image_path = os.path.join(save_path, "captured_image.jpg")
        
        for pose in self.waypoints:
            goal = self.goal_pose(pose)
            self.timer.start(5000)
            self.clear_global_costmap()
            
            move_client.send_goal(goal)
            move_client.wait_for_result()
            time.sleep(1)
            
            _, frame = self.cap.read()  # 새로운 프레임 읽어오기

            # 빨간색과 파란색 채널을 교체하여 RGB 형식으로 변환
            self.RGBframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
            self.RGBframe = cv2.cvtColor(self.RGBframe, cv2.COLOR_BGR2RGB)

            cv2.imwrite(image_path, self.RGBframe) 
            print(f"Image saved to: {save_path}")
            d = run(**vars(parse_opt()))
            self.abnormal += d

            print('count:', self.count)

            if self.count == len(self.waypoints):
                print("end")
                break

        print('촬영완료')
        print('%d개 이상검출' % self.abnormal)
        self.clear_global_costmap()
        self.finished.emit()


    def goal_pose(self, pose):  # <2>
        goal_pose = MoveBaseGoal()
        goal_pose.target_pose.header.frame_id = 'map'
        goal_pose.target_pose.pose.position.x = pose[0][0]
        print('positon.X', pose[0][0])
        goal_pose.target_pose.pose.position.y = pose[0][1]
        print('positon.y', pose[0][1])
        goal_pose.target_pose.pose.position.z = pose[0][2]
        print('positon.Z', pose[0][2])
        goal_pose.target_pose.pose.orientation.x = pose[1][0]
        print('orientation.X', pose[1][0])
        goal_pose.target_pose.pose.orientation.y = pose[1][1]
        print('orientation.Y', pose[1][1])
        goal_pose.target_pose.pose.orientation.z = pose[1][2]
        print('orientation.Z', pose[1][2])
        goal_pose.target_pose.pose.orientation.w = pose[1][3]
        print('orientation.W', pose[1][3])

        return goal_pose

    def handler(signum, frame):
        sys.exit(0)

    def clear_global_costmap(self):
        subprocess.call(["rosservice", "call", "/move_base/clear_costmaps"])

    # def save_image(self, save_path, frame):
    #     # 이미지를 저장할 경로와 파일명을 지정합니다.
    #     cv2.imwrite(save_path, frame)   

class ComeBack(QThread): # [복귀]
    waypoints = [  # <1>  #(세로, 가로, 0) , (방향)
    [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)]  
]

    def run(self):
        move_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        move_client.wait_for_server()
        
        for pose in self.waypoints:
            goal = self.goal_pose(pose)
            self.clear_global_costmap()
            move_client.send_goal(goal)
            move_client.wait_for_result()
            self.clear_global_costmap()


    def goal_pose(self, pose):  # <2>
        goal_pose = MoveBaseGoal()
        goal_pose.target_pose.header.frame_id = 'map'
        goal_pose.target_pose.pose.position.x = pose[0][0]
        print('positon.X', pose[0][0])
        goal_pose.target_pose.pose.position.y = pose[0][1]
        print('positon.y', pose[0][1])
        goal_pose.target_pose.pose.position.z = pose[0][2]
        print('positon.Z', pose[0][2])
        goal_pose.target_pose.pose.orientation.x = pose[1][0]
        print('orientation.X', pose[1][0])
        goal_pose.target_pose.pose.orientation.y = pose[1][1]
        print('orientation.Y', pose[1][1])
        goal_pose.target_pose.pose.orientation.z = pose[1][2]
        print('orientation.Z', pose[1][2])
        goal_pose.target_pose.pose.orientation.w = pose[1][3]
        print('orientation.W', pose[1][3])

        return goal_pose
    
    def clear_global_costmap(self):
        subprocess.call(["rosservice", "call", "/move_base/clear_costmaps"])
    
    def handler(signum, frame):
        sys.exit(0)


if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()

