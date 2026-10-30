"""
sim_recorder.py — TURTLE Robotics SI
======================================
Records teleoperation episodes from the Gazebo simulation into a dataset
that lerobot can use to train an ACT policy.

Each episode is a sequence of (observation, action) pairs sampled at a
fixed rate. The observation is the current joint state of the sim arm.
The action is the current joint command (what the teleop sent).

Usage
-----
  # Start recording (keyboard or leader bridge must be running separately):
  ros2 run turtle_control sim_recorder \
    --ros-args -p output_dir:=~/sim_dataset -p num_episodes:=50

  - Press SPACE to start a new episode.
  - Press SPACE again (or wait for episode_time_s) to end the episode.
  - Press Q to quit after saving all episodes.

  Episodes are saved as:
    ~/sim_dataset/
      episode_000/
        data.json        ← list of {t, obs, action} dicts
      episode_001/
        data.json
      ...
      dataset_info.json  ← metadata (joint names, fps, num_episodes)

After recording, convert to lerobot LeRobotDataset format with:
  python ~/ros2_ws/src/turtle_control/scripts/convert_to_lerobot.py \
    --input ~/sim_dataset --output ~/lerobot_dataset

Then train:
  cd ~/lerobot && conda activate lerobot
  python -m lerobot.scripts.train \
    --policy-path lerobot/configs/policy/act.yaml \
    --dataset-repo-id local/sim_dataset \
    --output-dir outputs/train/act_so101_sim
"""

import json
import math
import os
import sys
import select
import termios
import tty
import time
from pathlib import Path
from datetime import datetime

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64

JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]

JOINT_TOPICS = {
    "shoulder_pan":  "/so101/shoulder_pan",
    "shoulder_lift": "/so101/shoulder_lift",
    "elbow_flex":    "/so101/elbow_flex",
    "wrist_flex":    "/so101/wrist_flex",
    "wrist_roll":    "/so101/wrist_roll",
    "gripper":       "/so101/gripper",
}

RECORD_HZ    = 30
DEFAULT_SECS = 30


def get_key(settings, timeout=0.05):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    key = sys.stdin.read(1) if rlist else ""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class SimRecorder(Node):
    def __init__(self):
        super().__init__("sim_recorder")

        self.declare_parameter("output_dir",    "~/sim_dataset")
        self.declare_parameter("num_episodes",  50)
        self.declare_parameter("episode_time_s", DEFAULT_SECS)
        self.declare_parameter("fps",           RECORD_HZ)

        output_dir     = Path(self.get_parameter("output_dir").value).expanduser()
        self.num_eps   = self.get_parameter("num_episodes").value
        self.ep_secs   = self.get_parameter("episode_time_s").value
        self.fps       = self.get_parameter("fps").value

        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir

        # Current joint state (observation)
        self.obs = {j: 0.0 for j in JOINT_NAMES}

        # Current commanded positions (action) — tracked by shadowing teleop topics
        self.action = {j: 0.0 for j in JOINT_NAMES}

        # Subscribe to joint states from Gazebo
        self.create_subscription(
            JointState, "/so101/joint_states", self._joint_state_cb, 10
        )

        # Subscribe to each joint command topic to capture what the teleop sends
        for joint, topic in JOINT_TOPICS.items():
            self.create_subscription(
                Float64, topic,
                lambda msg, j=joint: self._action_cb(msg, j),
                10,
            )

        self.recording   = False
        self.episode_buf = []
        self.ep_index    = 0
        self.ep_start    = None

        self.get_logger().info(
            f"Recorder ready. Output: {output_dir}  "
            f"Episodes: {self.num_eps}  Duration: {self.ep_secs}s each."
        )

    def _joint_state_cb(self, msg: JointState):
        for i, name in enumerate(msg.name):
            if name in self.obs and i < len(msg.position):
                self.obs[name] = msg.position[i]

        if self.recording:
            elapsed = time.monotonic() - self.ep_start
            self.episode_buf.append({
                "t":      round(elapsed, 4),
                "obs":    {j: round(v, 6) for j, v in self.obs.items()},
                "action": {j: round(v, 6) for j, v in self.action.items()},
            })
            # Auto-stop when episode time is up
            if elapsed >= self.ep_secs:
                self._stop_episode()

    def _action_cb(self, msg: Float64, joint: str):
        self.action[joint] = msg.data

    def start_episode(self):
        if self.recording:
            self.get_logger().warn("Already recording.")
            return
        self.episode_buf = []
        self.ep_start    = time.monotonic()
        self.recording   = True
        print(f"\n▶  Episode {self.ep_index:03d} started. "
              f"Move the arm. Press SPACE to stop early.")

    def _stop_episode(self):
        if not self.recording:
            return
        self.recording = False
        ep_dir = self.output_dir / f"episode_{self.ep_index:03d}"
        ep_dir.mkdir(parents=True, exist_ok=True)
        data_path = ep_dir / "data.json"
        with open(data_path, "w") as f:
            json.dump(self.episode_buf, f)
        n = len(self.episode_buf)
        dur = round(self.episode_buf[-1]["t"], 2) if self.episode_buf else 0
        print(f"■  Episode {self.ep_index:03d} saved — {n} frames, {dur}s  →  {ep_dir}")
        self.ep_index += 1
        if self.ep_index >= self.num_eps:
            print(f"\nAll {self.num_eps} episodes recorded.")
            self._save_metadata()
            print("Done. Press Q to quit.")

    def _save_metadata(self):
        meta = {
            "joint_names":   JOINT_NAMES,
            "fps":           self.fps,
            "num_episodes":  self.ep_index,
            "episode_time_s": self.ep_secs,
            "created":       datetime.now().isoformat(),
        }
        with open(self.output_dir / "dataset_info.json", "w") as f:
            json.dump(meta, f, indent=2)
        print(f"Metadata saved to {self.output_dir}/dataset_info.json")


def main():
    rclpy.init()
    node = SimRecorder()

    print("""
╔═══════════════════════════════════════════════════╗
║        SO-101 Sim Recorder                        ║
╠═══════════════════════════════════════════════════╣
║  SPACE    Start / stop episode                    ║
║  Q        Quit and save                           ║
╚═══════════════════════════════════════════════════╝
Make sure keyboard_teleop or leader_bridge is running.
""")

    settings = termios.tcgetattr(sys.stdin)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0)
            key = get_key(settings)
            if key == " ":
                if node.recording:
                    node._stop_episode()
                elif node.ep_index < node.num_eps:
                    node.start_episode()
            elif key in ("q", "Q"):
                if node.recording:
                    node._stop_episode()
                node._save_metadata()
                break
    except KeyboardInterrupt:
        if node.recording:
            node._stop_episode()
        node._save_metadata()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
