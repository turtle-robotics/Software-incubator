#!/usr/bin/env python3
"""
TURTLE Robotics SI — Drive Turtle Node
======================================
Publishes Twist commands to the turtle_bot in Gazebo.

Students will modify this node to implement:
  - Week 6:  Drive forward/turn sequences (open-loop)
  - Week 9:  Odometry-based navigation (closed-loop)

Usage:
  ros2 run turtle_control drive_turtle

Topics published:
  /model/turtle_bot/cmd_vel  (geometry_msgs/Twist)

Topics subscribed:
  /model/turtle_bot/odom     (nav_msgs/Odometry)   [Week 9]
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class DriveTurtle(Node):
    """Open-loop drive node for the turtle_bot."""

    def __init__(self):
        super().__init__("drive_turtle")

        # Publisher: send velocity commands to the robot
        self.cmd_pub = self.create_publisher(
            Twist,
            "/model/turtle_bot/cmd_vel",
            10,
        )

        # Timer: publish at 10 Hz
        self.timer = self.create_timer(0.1, self.timer_callback)

        # Internal state — tracks which phase of the motion we are in
        self.elapsed = 0.0
        self.get_logger().info("DriveTurtle node started — publishing to /model/turtle_bot/cmd_vel")

    def timer_callback(self):
        """
        Called every 0.1 s.

        === STUDENT TASK (Week 6) ===
        Edit this function to make the robot:
          1. Drive forward at 0.3 m/s for 3 seconds
          2. Turn left at 0.5 rad/s for 2 seconds
          3. Stop

        Hint: use self.elapsed to track how long we have been running.
        """

        msg = Twist()
        self.elapsed += 0.1

        # ---- TODO: Replace the pattern below with your own sequence ----
        if self.elapsed < 3.0:
            # Phase 1: drive forward
            msg.linear.x = 0.3
            msg.angular.z = 0.0
        elif self.elapsed < 5.0:
            # Phase 2: turn left
            msg.linear.x = 0.0
            msg.angular.z = 0.5
        else:
            # Phase 3: stop
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        # ---- END TODO ----

        self.cmd_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = DriveTurtle()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
