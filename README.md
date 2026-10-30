# TURTLE Robotics SI — ROS 2 + Gazebo Workspace

A Docker-based ROS 2 Jazzy + Gazebo Harmonic environment for TURTLE Robotics
Supplemental Instruction (SI) sessions.  
Adapted from the POBS project structure.

---

## What's Inside

| Package | Purpose |
|---|---|
| `turtle_gazebo` | Gazebo world, `turtle_bot` SDF model, launch files |
| `turtle_control` | Python drive node — students edit this |

The **turtle_bot** is a differential-drive robot (orange body, two driven wheels,
two passive caster balls). It responds to `geometry_msgs/Twist` on
`/model/turtle_bot/cmd_vel`.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
  or Docker Engine (Linux)
- [Docker Compose](https://docs.docker.com/compose/) (bundled with Docker Desktop)

---

## Quick Start

### 1 — Build the image (one time)

```bash
docker compose build
```

### 2 — Start the container

```bash
docker compose up -d
docker compose exec ros bash
```

### 3 — Build the ROS 2 workspace (inside the container)

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### 4 — Launch Gazebo with the turtle_bot

```bash
ros2 launch turtle_gazebo simulation.launch.py
```

Gazebo opens, loads an empty world, and spawns the orange turtle_bot after ~3 s.

### 5 — Run the drive node (new terminal tab in the container)

```bash
docker compose exec ros bash
source ~/ros2_ws/install/setup.bash
ros2 run turtle_control drive_turtle
```

The robot drives forward for 3 s, turns left for 2 s, then stops.

---

## Useful Commands

### Check what topics are available

```bash
ros2 topic list
```

You should see `/model/turtle_bot/cmd_vel` and `/model/turtle_bot/odom`.

### Send a velocity command manually

```bash
# Drive forward at 0.2 m/s
ros2 topic pub --once /model/turtle_bot/cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}"

# Turn left at 0.5 rad/s
ros2 topic pub --once /model/turtle_bot/cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}"

# Stop
ros2 topic pub --once /model/turtle_bot/cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

### Echo odometry

```bash
ros2 topic echo /model/turtle_bot/odom
```

---

## Launch with the SO-101 Arm

To spawn both the turtle_bot and the SO-101 arm in the same world:

```bash
ros2 launch turtle_gazebo simulation_with_arm.launch.py
```

The arm spawns at x=1.0 m (to the right of the robot). Each joint is controlled
by its own topic and responds to `std_msgs/Float64` angle commands in radians.

### How Joint Control Works

Each joint is controlled by publishing an **angle in radians** to its topic.
You say "go to this angle" and the Gazebo PID controller moves the joint there smoothly.

| Joint | What it does | Range | Notes |
|---|---|---|---|
| `shoulder_pan` | Rotates the whole arm left/right (turntable) | -3.14 to +3.14 | `+1.57` = 90° left, `-1.57` = 90° right |
| `shoulder_lift` | Tilts upper arm forward/back | -1.57 to +1.57 | `0` = straight up, `-0.5` = leaning forward |
| `elbow_flex` | Bends the elbow | -2.70 to +2.70 | `+1.0` = bent inward |
| `wrist_flex` | Tilts the wrist up/down | -1.57 to +1.57 | `±1.0` = tilted |
| `wrist_roll` | Spins the wrist like a screwdriver | -3.14 to +3.14 | `+3.14` = full spin |
| `gripper` | Opens/closes the gripper | 0 to 1.57 | `0` = open, `1.57` = closed |

A single command moves one joint and holds it there:
```bash
# Move shoulder_pan to 0.5 rad and hold
ros2 topic pub --once /so101/shoulder_pan std_msgs/Float64 "data: 0.5"
```

In Python (inside `arm_control.py`) it is the same thing:
```python
self.send("shoulder_pan", 0.785)   # 45 degrees left
self.send("gripper", 1.57)         # close gripper
```

There are no arrow keys — just pick a joint, pick an angle, publish it.

---

### Control the arm manually

```bash
# Pan the base left 45 degrees
ros2 topic pub --once /so101/shoulder_pan std_msgs/Float64 "data: 0.785"

# Lift the shoulder
ros2 topic pub --once /so101/shoulder_lift std_msgs/Float64 "data: -0.5"

# Flex the elbow
ros2 topic pub --once /so101/elbow_flex std_msgs/Float64 "data: 0.8"

# Close the gripper
ros2 topic pub --once /so101/gripper std_msgs/Float64 "data: 1.57"

# Open the gripper
ros2 topic pub --once /so101/gripper std_msgs/Float64 "data: 0.0"
```

### Run the arm demo node

```bash
ros2 run turtle_control arm_control
```

Runs a 7-step sequence: home → pan → lift → flex elbow → close gripper →
open gripper → home.  Edit `arm_control.py`'s `run_sequence()` to make your own.

### Watch joint states

```bash
ros2 topic echo /so101/joint_states
```

---

## Week 6 — SI Exercise

**Goal:** Understand ROS 2 topics and open-loop robot motion.

Edit `ros2_ws/src/turtle_control/turtle_control/drive_turtle.py` and complete
the `timer_callback` function so the robot:

1. Drives **forward** at `0.3 m/s` for **3 seconds**
2. **Turns left** at `0.5 rad/s` for **2 seconds**
3. **Stops**

Then rebuild and run:

```bash
colcon build --symlink-install
ros2 run turtle_control drive_turtle
```

**Questions to answer:**
1. What message type does `cmd_vel` use? What are its fields?
2. What does `angular.z` positive vs negative do?
3. What happens if you increase `linear.x` to `1.0`?

---

## Week 9 — SI Exercise (Advanced)

**Goal:** Use odometry feedback for closed-loop control.

Extend `drive_turtle.py` to subscribe to `/model/turtle_bot/odom` and:

1. Drive forward **exactly 1 meter** (use position feedback to stop)
2. Turn **exactly 90 degrees** (use orientation feedback to stop)

Skeleton to get you started:

```python
from nav_msgs.msg import Odometry
import math

# In __init__:
self.odom_sub = self.create_subscription(Odometry, "/model/turtle_bot/odom", self.odom_callback, 10)
self.current_x = 0.0
self.current_y = 0.0
self.current_yaw = 0.0

# New callback:
def odom_callback(self, msg):
    self.current_x = msg.pose.pose.position.x
    self.current_y = msg.pose.pose.position.y
    # Convert quaternion → yaw
    q = msg.pose.pose.orientation
    self.current_yaw = math.atan2(
        2*(q.w*q.z + q.x*q.y),
        1 - 2*(q.y**2 + q.z**2)
    )
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `colcon build` fails with "package not found" | Run `rosdep update && rosdep install --from-paths src -i -y` first |
| Gazebo opens but robot doesn't appear | Wait 5 s; the spawn is delayed. Check the terminal for spawn errors. |
| `/model/turtle_bot/cmd_vel` not in `ros2 topic list` | The robot hasn't spawned yet, or Gazebo crashed. Restart the launch. |
| `docker compose build` is very slow | Normal on first build — the image is ~2 GB. Subsequent builds are cached. |

---

## File Structure

```
turtle-si/
├── Dockerfile                          # ROS 2 Jazzy + Gazebo Harmonic image
├── compose.yaml                        # Main Docker Compose file
├── compose.gui-wslg.yaml               # WSLg / X11 overlay for GUI on Windows
├── docker/
│   └── entrypoint.sh
└── ros2_ws/
    └── src/
        ├── turtle_gazebo/              # Simulation package
        │   ├── launch/
        │   │   ├── simulation.launch.py            ← robot only
        │   │   └── simulation_with_arm.launch.py   ← robot + arm
        │   ├── models/
        │   │   ├── turtle_bot/
        │   │   │   ├── model.config
        │   │   │   └── model.sdf       ← diff-drive robot
        │   │   └── so101_arm/
        │   │       ├── model.config
        │   │       └── model.sdf       ← 6-DOF arm
        │   └── worlds/
        │       └── empty.sdf
        └── turtle_control/             # Student code lives here
            └── turtle_control/
                ├── drive_turtle.py     ← EDIT THIS (Week 6)
                └── arm_control.py      ← EDIT THIS (Week 9)
```
