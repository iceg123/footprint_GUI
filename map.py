import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
import rospy
import actionlib
import time
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import subprocess

class SecondaryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("route")

        # Load the image
        self.image_label = QLabel(self)
        pixmap = QPixmap("map_final.jpg")
        pixmap = pixmap.scaledToWidth(300)
        self.image_label.setPixmap(pixmap)

        # Create layout for buttons and image
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)

        grid_layout = QGridLayout()

        # Create buttons "one points", "two points", and "three points"
        button_labels = ["one points", "two points", "three points","cancel"]
        positions = [(i, j) for i in range(2) for j in range(2)]
        for label, position in zip(button_labels, positions):
            button = QPushButton(label)
            button.clicked.connect(lambda ch, lbl=label: self.on_button_clicked(lbl))
            button.setFixedSize(5 * 30, 2 * 30)  # Set width and height
            grid_layout.addWidget(button, *position)
            font = button.font()
            font.setPointSize(15) 
            button.setFont(font)
        layout.addLayout(grid_layout)
        grid_layout.addWidget(button, *position)
        # Create a widget and set layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.waypoints = []  # Initialize waypoints list
        self.current_waypoint_index = 0  # Initialize waypoint index
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.move_to_next_waypoint)

    def on_button_clicked(self, button_label):
        if button_label == "one points":
            self.waypoints = [
                [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)]
            ]
        if button_label == "two points":
            self.waypoints = [
                [(15.55, -4.9, 0.0, 0.0, 0.0, -0.7, 0.7)]
            ]
        if button_label == "three points":
            self.waypoints = [
                [(15.55, -9.6, 0.0, 0.0, 0.0, 0.7, 0.7)]
            ]
        if button_label == "cancel":
            sys.exit(0)
        self.current_waypoint_index = 0  # Reset waypoint index
        self.move_to_next_waypoint()

    def move_to_next_waypoint(self):
        self.clear_global_costmap()
        move_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        move_client.wait_for_server()

        # Check if reached the last waypoint
        if self.current_waypoint_index == len(self.waypoints):
            print("Reached the final waypoint")
            self.waypoints = []  # Reset waypoints after reaching
            return

        for pose in self.waypoints[self.current_waypoint_index]:
            goal = self.goal_pose(pose)
            move_client.send_goal(goal)
            sys.exit(0)

        self.current_waypoint_index += 1  # Move to the next waypoint
        self.clear_global_costmap()

    
    def goal_pose(self, pose):
        goal_pose = MoveBaseGoal()
        goal_pose.target_pose.header.frame_id = 'map'
        goal_pose.target_pose.pose.position.x = pose[0]
        goal_pose.target_pose.pose.position.y = pose[1]
        goal_pose.target_pose.pose.position.z = pose[2]
        goal_pose.target_pose.pose.orientation.x = pose[3]
        goal_pose.target_pose.pose.orientation.y = pose[4]
        goal_pose.target_pose.pose.orientation.z = pose[5]
        goal_pose.target_pose.pose.orientation.w = pose[6]
        return goal_pose

    def clear_global_costmap(self):
        subprocess.call(["rosservice", "call", "/move_base/clear_costmaps"])

def main():
    rospy.init_node('second_GUI')
    app = QApplication([])
    secondary_window = SecondaryWindow()
    secondary_window.show()
    app.exec_()

if __name__ == "__main__":
    main()
