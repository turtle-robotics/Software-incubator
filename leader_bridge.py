"""
leader_bridge.py — TURTLE Robotics SI
=======================================
Reads the SO-101 physical leader arm over USB and forwards its joint
positions as Float64 commands to the Gazebo simulation in real time.

Use this in the lab when you have both the leader arm and a laptop
running the simulation.

Usage
-----
  ros2 run turtle_control leader_bridge --ros-args \
    -p port:=/dev/ttyACM1 \
    -p robot_id:=so_leader

  # Windows example:
  ros2 run turtle_control leader_bridge --ros-args \
    -p port:=COM5 \
    -p robot_id:=so_leader

Requirements
------------
  conda activate lerobot   (lerobot must be installed in the active env)
  The leader arm must already be calibrated (lerobot-calibrate).

How it works
------------
  - Connects to the leader arm via lerobot's FeetechMotorsBus
  - Reads all 6 joint positions at ~30 Hz
  - Maps them to the Gazebo /so101/* topics
  - The Gazebo JointPositionController moves the sim arm to match
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

# Joint name → Gazebo topic
JOINT_TOPICS = {
    "shoulder_pan":  "/so101/shoulder_pan",
    "shoulder_lift": "/so101/shoulder_lift",
    "elbow_flex":    "/so101/elbow_flex",
    "wrist_flex":    "/so101/wrist_flex",
    "wrist_roll":    "/so101/wrist_roll",
    "gripper":       "/so101/gripper",
}

# lerobot motor name → ROS joint name
# Adjust these if your calibration file uses different motor names.
MOTOR_MAP = {
    "shoulder_pan":  "shoulder_pan",
    "shoulder_lift": "shoulder_lift",
    "elbow_flex":    "elbow_flex",
    "wrist_flex":    "wrist_flex",
    "wrist_roll":    "wrist_roll",
    "gripper":       "gripper",
}

READ_HZ = 30   # leader arm polling rate


class LeaderBridge(Node):
    def __init__(self):
        super().__init__("leader_bridge")

        # Parameters
        self.declare_parameter("port",     "/dev/ttyACM1")
        self.declare_parameter("robot_id", "so_leader")
        self.declare_parameter("hz",       READ_HZ)

        port     = self.get_parameter("port").value
        robot_id = self.get_parameter("robot_id").value
        hz       = self.get_parameter("hz").value

        # Publishers
        self.pubs = {
            joint: self.create_publisher(Float64, topic, 10)
            for joint, topic in JOINT_TOPICS.items()
        }

        # Connect to leader arm
        try:
            from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
        except ImportError:
            self.get_logger().error(
                "lerobot is not installed or the conda environment is not active. "
                "Activate it with: conda activate lerobot"
            )
            raise SystemExit(1)

        motor_names  = list(MOTOR_MAP.keys())
        motor_models = ["sts3215"] * len(motor_names)
        motor_ids    = list(range(1, len(motor_names) + 1))

        self.bus = FeetechMotorsBus(
            port=port,
            motors={
                name: (mid, model)
                for name, mid, model in zip(motor_names, motor_ids, motor_models)
            },
        )
        self.bus.connect()
        self.get_logger().info(
            f"Leader arm connected on {port} (id={robot_id}). "
            f"Bridging to Gazebo at {hz} Hz."
        )

        self.timer = self.create_timer(1.0 / hz, self.read_and_publish)

    def read_and_publish(self):
        try:
            # Read present positions from all motors (returns dict name→degrees)
            positions = self.bus.read("Present_Position")
        except Exception as e:
            self.get_logger().warn(f"Read error: {e}")
            return

        for motor_name, ros_joint in MOTOR_MAP.items():
            if motor_name not in positions:
                continue
            # Convert degrees (lerobot native) to radians for Gazebo
            import math
            angle_rad = math.radians(positions[motor_name])

            msg = Float64()
            msg.data = float(angle_rad)
            self.pubs[ros_joint].publish(msg)

    def destroy_node(self):
        try:
            self.bus.disconnect()
        except Exception:
            pass
        super().destroy_node()


def main():
    rclpy.init()
    try:
        node = LeaderBridge()
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
