#!/usr/bin/env python3
"""
TURTLE Robotics SI — SO-101 Arm Control Node
=============================================
Sends position commands (radians) to each joint of the SO-101 arm
running in Gazebo.

Usage:
  ros2 run turtle_control arm_control

Topics published (one per joint):
  /so101/shoulder_pan   (std_msgs/Float64)
  /so101/shoulder_lift  (std_msgs/Float64)
  /so101/elbow_flex     (std_msgs/Float64)
  /so101/wrist_flex     (std_msgs/Float64)
  /so101/wrist_roll     (std_msgs/Float64)
  /so101/gripper        (std_msgs/Float64)

Topics subscribed:
  /so101/joint_states   (sensor_msgs/JointState)

Useful standalone commands (no node needed):
  # Move shoulder_pan to 0.5 rad
  ros2 topic pub --once /so101/shoulder_pan std_msgs/Float64 "data: 0.5"

  # Open gripper (0 = fully open)
  ros2 topic pub --once /so101/gripper std_msgs/Float64 "data: 0.0"

  # Close gripper (1.57 rad = ~90 deg)
  ros2 topic pub --once /so101/gripper std_msgs/Float64 "data: 1.57"
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import math
import time


# Joint names and their Gazebo topic
JOINTS = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]


class ArmControl(Node):
    """Publishes a pre-programmed joint sequence to the SO-101 arm."""

    def __init__(self):
        super().__init__("arm_control")

        # Create one publisher per joint
        self.publishers = {
            joint: self.create_publisher(Float64, f"/so101/{joint}", 10)
            for joint in JOINTS
        }

        self.get_logger().info("ArmControl node started.")
        self.get_logger().info("Publishing to: " + ", ".join(f"/so101/{j}" for j in JOINTS))

        # Run the demo sequence once, then hold position
        self.run_sequence()

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def send(self, joint: str, angle_rad: float):
        """Send a single joint position command."""
        msg = Float64()
        msg.data = float(angle_rad)
        self.publishers[joint].publish(msg)

    def home(self):
        """Move all joints to the home (zero) position."""
        for joint in JOINTS:
            self.send(joint, 0.0)

    def sleep(self, seconds: float):
        """Blocking sleep that keeps the node alive."""
        end = time.time() + seconds
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    # ------------------------------------------------------------------
    # Demo sequence  — STUDENTS EDIT THIS
    # ------------------------------------------------------------------
    def run_sequence(self):
        """
        Pre-programmed arm motion sequence.

        === STUDENT TASK (Week 9) ===
        Modify this sequence to:
          1. Move the arm to a "ready" pose (shoulder_lift = -0.5 rad)
          2. Extend the elbow (elbow_flex = 0.8 rad)
          3. Close the gripper (gripper = 1.57 rad)
          4. Return to home

        Angles are in RADIANS.
        Positive/negative directions match the real SO-101 hardware.
        """

        self.get_logger().info("Step 1: Home position")
        self.home()
        self.sleep(2.0)

        self.get_logger().info("Step 2: Pan left 45 deg")
        self.send("shoulder_pan", math.radians(45))
        self.sleep(2.0)

        self.get_logger().info("Step 3: Lift shoulder up")
        self.send("shoulder_lift", math.radians(-30))
        self.sleep(2.0)

        self.get_logger().info("Step 4: Flex elbow")
        self.send("elbow_flex", math.radians(60))
        self.sleep(2.0)

        self.get_logger().info("Step 5: Close gripper")
        self.send("gripper", 1.57)
        self.sleep(2.0)

        self.get_logger().info("Step 6: Open gripper")
        self.send("gripper", 0.0)
        self.sleep(1.5)

        self.get_logger().info("Step 7: Return to home")
        self.home()
        self.sleep(2.0)

        self.get_logger().info("Sequence complete. Holding position.")


def main(args=None):
    rclpy.init(args=args)
    node = ArmControl()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
