#!/usr/bin/env python3
"""
arm_keyboard_teleop.py  —  Keyboard teleoperation for the SO-101 arm in Gazebo
===============================================================================
Controls
--------
  1-6        Select joint  (1=shoulder_pan, 2=shoulder_lift, 3=elbow_flex,
                             4=wrist_flex,  5=wrist_roll,   6=gripper)
  W / Up     Increment selected joint position by STEP radians
  S / Down   Decrement selected joint position by STEP radians
  Space      Toggle gripper open (0 rad) / closed (0.6 rad)
  R          Reset all joints to home position (all zeros)
  Q / Esc    Quit

Topics published (std_msgs/Float64)
  /so101/shoulder_pan
  /so101/shoulder_lift
  /so101/elbow_flex
  /so101/wrist_flex
  /so101/wrist_roll
  /so101/gripper

Usage (after colcon build --symlink-install):
  ros2 run turtle_control arm_keyboard_teleop

Or from the launch file:
  ros2 launch turtle_gazebo arm_teleop.launch.py mode:=keyboard
"""

import sys
import tty
import termios
import threading
import select

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

# ── Joint configuration ──────────────────────────────────────────────────────

JOINTS = [
    ("shoulder_pan",   -3.14, 3.14),   # 1
    ("shoulder_lift",  -1.57, 1.57),   # 2
    ("elbow_flex",     -2.70, 2.70),   # 3
    ("wrist_flex",     -1.57, 1.57),   # 4
    ("wrist_roll",     -3.14, 3.14),   # 5
    ("gripper",         0.0,  0.6),    # 6  (0 = open, 0.6 = closed)
]

STEP       = 0.05   # radians per keypress
GRIPPER_OPEN   = 0.0
GRIPPER_CLOSED = 0.6

HELP = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SO-101 Arm Keyboard Teleop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Keys:
    1-6     Select joint
    W/↑     Increment joint (+{step} rad)
    S/↓     Decrement joint (-{step} rad)
    Space   Toggle gripper open/closed
    R       Reset all joints to home
    Q/Esc   Quit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Joints:
    1  shoulder_pan
    2  shoulder_lift
    3  elbow_flex
    4  wrist_flex
    5  wrist_roll
    6  gripper
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(step=STEP)


# ── Terminal helpers ──────────────────────────────────────────────────────────

def get_key(settings, timeout=0.1):
    """Read a single keypress in raw mode; return '' on timeout."""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    key = ''
    if rlist:
        key = sys.stdin.read(1)
        # Swallow additional bytes for arrow-key escape sequences
        if key == '\x1b':
            rlist2, _, _ = select.select([sys.stdin], [], [], 0.05)
            if rlist2:
                key2 = sys.stdin.read(1)
                if key2 == '[':
                    rlist3, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if rlist3:
                        key3 = sys.stdin.read(1)
                        return '\x1b[' + key3   # e.g. '\x1b[A' = Up arrow
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


# ── ROS 2 node ───────────────────────────────────────────────────────────────

class ArmKeyboardTeleop(Node):
    def __init__(self):
        super().__init__('arm_keyboard_teleop')

        # Publishers — one per joint, topic /so101/<joint_name>
        self._pubs = {}
        for name, _, _ in JOINTS:
            self._pubs[name] = self.create_publisher(
                Float64, f'/so101/{name}', 10)

        # Joint state: positions initialised to home (0 rad)
        self._pos = {name: 0.0 for name, _, _ in JOINTS}
        self._selected = 0   # index into JOINTS list
        self._gripper_closed = False

        # Publish home position immediately so arm isn't dangling
        self._publish_all()

        self.get_logger().info('arm_keyboard_teleop ready — check the terminal for controls.')

    # ── Publishing ────────────────────────────────────────────────────────────

    def _publish_all(self):
        for name, _, _ in JOINTS:
            msg = Float64()
            msg.data = self._pos[name]
            self._pubs[name].publish(msg)

    def _publish_one(self, name: str):
        msg = Float64()
        msg.data = self._pos[name]
        self._pubs[name].publish(msg)

    # ── Key handling ─────────────────────────────────────────────────────────

    def handle_key(self, key: str) -> bool:
        """Process key; return False if the node should exit."""
        name, lo, hi = JOINTS[self._selected]

        # Joint selection
        if key in '123456':
            self._selected = int(key) - 1
            jname = JOINTS[self._selected][0]
            print(f'\r  → Joint {key}: {jname}  (pos={self._pos[jname]:.3f} rad)   ')

        # Increment
        elif key in ('w', 'W', '\x1b[A'):       # W or Up arrow
            self._pos[name] = min(hi, self._pos[name] + STEP)
            self._publish_one(name)
            print(f'\r  {name}: {self._pos[name]:+.3f} rad   ', end='', flush=True)

        # Decrement
        elif key in ('s', 'S', '\x1b[B'):       # S or Down arrow
            self._pos[name] = max(lo, self._pos[name] - STEP)
            self._publish_one(name)
            print(f'\r  {name}: {self._pos[name]:+.3f} rad   ', end='', flush=True)

        # Gripper toggle
        elif key == ' ':
            self._gripper_closed = not self._gripper_closed
            self._pos['gripper'] = GRIPPER_CLOSED if self._gripper_closed else GRIPPER_OPEN
            self._publish_one('gripper')
            state = 'CLOSED' if self._gripper_closed else 'OPEN'
            print(f'\r  gripper: {state} ({self._pos["gripper"]:.2f} rad)   ', end='', flush=True)

        # Reset
        elif key in ('r', 'R'):
            for jname, _, _ in JOINTS:
                self._pos[jname] = 0.0
            self._gripper_closed = False
            self._publish_all()
            print('\r  ★ All joints reset to home (0 rad)   ', end='', flush=True)

        # Quit
        elif key in ('q', 'Q', '\x03', '\x1b'):
            return False

        return True


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = ArmKeyboardTeleop()

    # Spin ROS in background thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    # Keyboard loop runs in the main thread (needs terminal stdin)
    settings = termios.tcgetattr(sys.stdin)
    print(HELP)
    print(f'  Active joint: 1 — shoulder_pan\n')

    running = True
    try:
        while running and rclpy.ok():
            key = get_key(settings)
            if key:
                running = node.handle_key(key)
    except Exception as exc:
        node.get_logger().error(f'Keyboard loop error: {exc}')
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()
        print('\n  arm_keyboard_teleop stopped.')


if __name__ == '__main__':
    main()
