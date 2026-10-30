"""
keyboard_teleop.py — TURTLE Robotics SI
========================================
Keyboard teleoperation for the SO-101 arm in Gazebo simulation.
Use this at home when you don't have the physical leader arm.

Controls
--------
  Joint selection:   1  2  3  4  5  6   (shoulder_pan … gripper)
  Move joint:        ↑ / ↑  increase angle   ↓ / ↓  decrease angle
  Home all joints:   H
  Quit:              Q or Ctrl-C

The selected joint is highlighted in the terminal status line.
Each keypress increments the joint by STEP_RAD (default 0.05 rad ≈ 3 deg).

Usage
-----
  ros2 run turtle_control keyboard_teleop
"""

import sys
import select
import termios
import tty
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

# ── Joint configuration ────────────────────────────────────────────────────
JOINTS = [
    ("shoulder_pan",  "/so101/shoulder_pan",  -3.14,  3.14),
    ("shoulder_lift", "/so101/shoulder_lift", -1.57,  1.57),
    ("elbow_flex",    "/so101/elbow_flex",    -2.70,  2.70),
    ("wrist_flex",    "/so101/wrist_flex",    -1.57,  1.57),
    ("wrist_roll",    "/so101/wrist_roll",    -3.14,  3.14),
    ("gripper",       "/so101/gripper",        0.00,  1.57),
]

STEP_RAD   = 0.05      # radians per keypress
PUBLISH_HZ = 20        # Hz — how often to re-publish current positions

KEY_UP    = "\x1b[A"
KEY_DOWN  = "\x1b[B"
KEY_JOINTS = "123456"
KEY_HOME  = "hH"
KEY_QUIT  = "qQ"

HELP = """
╔══════════════════════════════════════════════════╗
║        SO-101 Keyboard Teleop (Sim mode)         ║
╠══════════════════════════════════════════════════╣
║  1-6      Select joint                           ║
║  ↑ / ↓    Increase / decrease angle (0.05 rad)  ║
║  H        Move all joints to home (0 rad)        ║
║  Q        Quit                                   ║
╚══════════════════════════════════════════════════╝
"""


def get_key(settings):
    """Read one keypress (blocking, 0.1 s timeout). Returns '' on timeout."""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
        if key == "\x1b":          # escape sequence (arrow keys)
            key += sys.stdin.read(2)
    else:
        key = ""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__("keyboard_teleop")
        self.publishers_ = {}
        for name, topic, lo, hi in JOINTS:
            self.publishers_[name] = self.create_publisher(Float64, topic, 10)

        self.positions   = {name: 0.0 for name, _, _, _ in JOINTS}
        self.selected    = 0          # index into JOINTS list
        self.timer       = self.create_timer(1.0 / PUBLISH_HZ, self._publish_all)

    def _publish_all(self):
        for name, _, _, _ in JOINTS:
            msg = Float64()
            msg.data = self.positions[name]
            self.publishers_[name].publish(msg)

    def move(self, delta):
        name, _, lo, hi = JOINTS[self.selected]
        self.positions[name] = clamp(self.positions[name] + delta, lo, hi)

    def home(self):
        for name, _, _, _ in JOINTS:
            self.positions[name] = 0.0

    def status_line(self):
        parts = []
        for i, (name, _, _, _) in enumerate(JOINTS):
            angle = self.positions[name]
            marker = "►" if i == self.selected else " "
            parts.append(f"{marker}J{i+1} {name[:10]:<10} {angle:+.3f}")
        return "\n".join(parts)


def main():
    rclpy.init()
    node = KeyboardTeleop()

    print(HELP)
    settings = termios.tcgetattr(sys.stdin)

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0)
            key = get_key(settings)

            if key in KEY_QUIT:
                break
            elif key in KEY_JOINTS:
                node.selected = int(key) - 1
            elif key == KEY_UP:
                node.move(+STEP_RAD)
            elif key == KEY_DOWN:
                node.move(-STEP_RAD)
            elif key in KEY_HOME:
                node.home()

            # Redraw status (simple terminal overwrite)
            lines = node.status_line().split("\n")
            sys.stdout.write(f"\r\033[{len(lines)}A")   # move cursor up
            for line in lines:
                sys.stdout.write(f"\r\033[K{line}\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()
        print("\nTeleop stopped.")


if __name__ == "__main__":
    main()
