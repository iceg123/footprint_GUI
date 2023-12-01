import sys
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt, QThread
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
import pyzbar.pyzbar as pyzbar
from playsound import playsound
import time
import pymysql
import subprocess

# 커스텀 코드 임포트
from BoxDamageDetect.detect import *

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
        loadUi("main4.ui", self)
        rospy.init_node('my_patrol')

        # QWidget.showFullScreen(self) # 전체화면
        self.cap = cv2.VideoCapture(0)
        # self.cap = cv2.VideoCapture("http://192.168.123.16:4747/video")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        # self.btn_Camera.clicked.connect(self.search)
        self.btn_Camera.clicked.connect(self.photo)
        self.btn_Inspection.clicked.connect(self.inspect)
        self.btn_Send.clicked.connect(self.transfer)
    

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

    # def search(self): # [촬영] (원본)
    #     d = run(**vars(parse_opt()))
    #     if(d != 0):
    #         self.textEdit.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
    #         self.textEdit.setText("손상 의심")
    #         playsound("wrong.mp3")
    #     else:
    #         self.textEdit.setStyleSheet("color: #000000;" "background-color: #00FF00;" "font: 30pt")
    #         self.textEdit.setText("이상 없음")
    #     print('%d개 이상검출' %d)
        
    def search(self): # [촬영] (수정본)
        
        
        move_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)  # <3>
        move_client.wait_for_server()
        count = 0
        save_path = "./BoxDamageDetect/test/captured_image.jpg"
        abnormal = 0
        for pose in Patrol.waypoints:   # <4>
            _, self.frame = self.cap.read()
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB
                                      )
            goal = Patrol.goal_pose(pose)
            move_client.send_goal(goal) #목표지점을 보냄
            move_client.wait_for_result() #목표지점에 도달할때까지 대기
            time.sleep(1) #1초동안 대기 

            # 추가
            
            Patrol.save_image(self.frame, save_path)  # 여기에 사진을 저장하는 내용 추가
            # self.update()  # 이미지 업데이트
            d = run(**vars(parse_opt()))
            abnormal += d
            # 추가
            if(d != 0):
                self.textEdit.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
                self.textEdit.setText("손상 의심")
                count += 1
            else:
                self.textEdit.setStyleSheet("color: #000000;" "background-color: #00FF00;" "font: 30pt")
                self.textEdit.setText("이상 없음")
                
            # if(count-1 == waypoints.index([(-1.0, -9.0, 0.0), (0.0, 0.0, 0.0, 1.0)])):
            print('count:', count)
            # time.sleep(3)
            if count == len(Patrol.waypoints):
                print("end")
                break
        print('촬영완료')
        
        print('%d개 이상검출' %abnormal)

    def inspect(self):
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
            self.codeInfo.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
            self.codeInfo.setText("검출불가")
            playsound("wrong.mp3")

            # self.brandInfo.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 60pt")
            # self.brandInfo.setText("Brand not found")
        else:
            print(code)
            self.codeInfo.setStyleSheet("color: #FFFFFF;" "background-color: #8080FF;")
            self.codeInfo.setText(code_lite)
            code = 'None'

            if result:
                brand_name = result[0:2]
                self.brandInfo.setStyleSheet("color: #FFFFFF;" "background-color: #8080FF;")
                self.brandInfo.setText(f"{brand_name}")
            else:
                self.brandInfo.setStyleSheet("color: #FFFF00;" "background-color: #FF0000;" "font: 30pt")
                self.brandInfo.setText("검출불가")

    def send_image(self):
        _, frame = self.cap.read()

    # Convert the frame to bytes
        _, img_encoded = cv2.imencode('.jpg', frame)
        image_data = img_encoded.tobytes()

        # Replace 'your_server_endpoint' with the actual endpoint to which you want to send the image
        server_endpoint = 'http://your_server_endpoint'

    # Make a POST request to the server to send the image
        try:
            response = requests.post(server_endpoint, files={'image': image_data})
            response.raise_for_status()  # Raise an exception for HTTP errors
            print("Image sent successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Error sending image: {e}")

    def transfer(self): # [전송]
        subprocess.call(["mv", "/home/ubuntu/bot/BoxDamageDetect/runs/detect", "/home/share"])
        self.textEdit.setStyleSheet("color: #000000;" "background-color: #00FF00;" "font: 30pt")
        self.textEdit.setText("전송 완료")

class Patrol(QThread):
    # [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)] 시작위치
    # waypoints = [  # <1> 
    #     [(13.0, -7.0, 0.0), (0.0, 0.0, 0.0, 1.0)],  #좌표, 바라보는 방향
    #     [(13.0, -7.7, 0), (0.0, 0.0, -0.7, 0.7)],
    #     [(13.0, -8.4, 0), (0.0, 0.0, -1.0, 0.0)],
    #     [(13.0, -7.7, 0), (0.0, 0.0, 0.7, 0.7)],
    #     [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)],
    #     [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)]
    # ]

    waypoints = [  # <1> 
        [(1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)],  #좌표, 바라보는 방향
        [(2.0, 0.0, 0.0), (0.0, 0.0, -0.7, 0.7)],
        [(3.0, 0.0, 0.0), (0.0, 0.0, -1.0, 0.0)],
        [(4.0, 0.0, 0.0), (0.0, 0.0, 0.7, 0.7)],
        [(0.5, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)]
    ]

    def goal_pose(pose):  # <2>
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

    def save_image(frame, save_path):
        # 이미지를 저장할 경로와 파일명을 지정합니다.
        cv2.imwrite(save_path, frame)        

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()

