#!/usr/bin/env python3
import sys, tty, termios, threading, select
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

JOINTS = [
    ("shoulder_pan",  -3.14, 3.14),
    ("shoulder_lift", -1.57, 1.57),
    ("elbow_flex",    -2.70, 2.70),
    ("wrist_flex",    -1.57, 1.57),
    ("wrist_roll",    -3.14, 3.14),
    ("gripper",        0.0,  0.6),
]
STEP = 0.05
HELP = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SO-101 Arm Keyboard Teleop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1-6     Select joint
  W/Up    Increment (+0.05 rad)
  S/Down  Decrement (-0.05 rad)
  Space   Toggle gripper open/closed
  R       Reset all to home (0 rad)
  Q/Esc   Quit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1=shoulder_pan  2=shoulder_lift
  3=elbow_flex    4=wrist_flex
  5=wrist_roll    6=gripper
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def get_key(settings, timeout=0.1):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    key = ''
    if rlist:
        key = sys.stdin.read(1)
        if key == '\x1b':
            r2, _, _ = select.select([sys.stdin], [], [], 0.05)
            if r2:
                k2 = sys.stdin.read(1)
                if k2 == '[':
                    r3, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if r3:
                        return '\x1b[' + sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

class ArmKeyboardTeleop(Node):
    def __init__(self):
        super().__init__('arm_keyboard_teleop')
        self._pubs = {name: self.create_publisher(Float64, f'/so101/{name}', 10)
                      for name, _, _ in JOINTS}
        self._pos = {name: 0.0 for name, _, _ in JOINTS}
        self._selected = 0
        self._gripper_closed = False
        self._publish_all()

    def _publish_all(self):
        for name, _, _ in JOINTS:
            msg = Float64(); msg.data = self._pos[name]
            self._pubs[name].publish(msg)

    def _publish_one(self, name):
        msg = Float64(); msg.data = self._pos[name]
        self._pubs[name].publish(msg)

    def handle_key(self, key):
        name, lo, hi = JOINTS[self._selected]
        if key in '123456':
            self._selected = int(key) - 1
            jname = JOINTS[self._selected][0]
            print(f'\r  Joint {key}: {jname}  pos={self._pos[jname]:.3f}   ')
        elif key in ('w', 'W', '\x1b[A'):
            self._pos[name] = min(hi, self._pos[name] + STEP)
            self._publish_one(name)
            print(f'\r  {name}: {self._pos[name]:+.3f} rad   ', end='', flush=True)
        elif key in ('s', 'S', '\x1b[B'):
            self._pos[name] = max(lo, self._pos[name] - STEP)
            self._publish_one(name)
            print(f'\r  {name}: {self._pos[name]:+.3f} rad   ', end='', flush=True)
        elif key == ' ':
            self._gripper_closed = not self._gripper_closed
            self._pos['gripper'] = 0.6 if self._gripper_closed else 0.0
            self._publish_one('gripper')
            state = 'CLOSED' if self._gripper_closed else 'OPEN'
            print(f'\r  gripper: {state}   ', end='', flush=True)
        elif key in ('r', 'R'):
            for jname, _, _ in JOINTS: self._pos[jname] = 0.0
            self._gripper_closed = False
            self._publish_all()
            print('\r  Reset to home   ', end='', flush=True)
        elif key in ('q', 'Q', '\x03', '\x1b'):
            return False
        return True

def main(args=None):
    rclpy.init(args=args)
    node = ArmKeyboardTeleop()
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()
    settings = termios.tcgetattr(sys.stdin)
    print(HELP)
    running = True
    try:
        while running and rclpy.ok():
            key = get_key(settings)
            if key: running = node.handle_key(key)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node(); rclpy.shutdown()
        print('\nStopped.')

if __name__ == '__main__':
    main()
