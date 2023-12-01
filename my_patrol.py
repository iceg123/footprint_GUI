#!/usr/bin/env python3

import cv2
import rospy
import actionlib
import time, signal, sys
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from BoxDamageDetect.detect import *

class patrol():
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
        goal_pose.target_pose.pose.position.y = pose[0][1]
        goal_pose.target_pose.pose.position.z = pose[0][2]
        goal_pose.target_pose.pose.orientation.x = pose[1][0]
        goal_pose.target_pose.pose.orientation.y = pose[1][1]
        goal_pose.target_pose.pose.orientation.z = pose[1][2]
        goal_pose.target_pose.pose.orientation.w = pose[1][3]

        return goal_pose

    def handler(signum, frame):
        sys.exit(0)

    def save_image(frame, save_path):
        cv2.imwrite(save_path, frame)

if __name__ == '__main__':
    rospy.init_node('my_patrol')

    move_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    move_client.wait_for_server()
    count = 0
    save_path = "./BoxDamageDetect/test/captured_image.jpg"

    # cap = cv2.VideoCapture(0)  # 초기화 단계에서 카메라 객체 생성

    for pose in patrol.waypoints:
        goal = patrol.goal_pose(pose)
        move_client.send_goal(goal)
        move_client.wait_for_result()
        time.sleep(1)

        # _, frame = cap.read()  # 이미지 읽기
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # patrol.save_image(frame, save_path)
        # d = run(**vars(parse_opt()))

        count += 1
        print('count:', count)
        print(len(patrol.waypoints))
        if count == len(patrol.waypoints):
            print("end")
            break

        time.sleep(3)
        
        signal.signal(signal.SIGINT, patrol.handler)
    
    sys.exit(0)