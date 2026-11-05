"""
arm_teleop.launch.py  —  SO-101 arm pickup lab launcher
========================================================
Starts the arm_lab Gazebo world, spawns the SO-101 arm on the table,
then launches either keyboard or leader-arm control.

Usage
-----
  # Keyboard control (default)
  ros2 launch turtle_gazebo arm_teleop.launch.py

  # Leader arm control (physical leader arm plugged in via USB)
  ros2 launch turtle_gazebo arm_teleop.launch.py mode:=leader

Arguments
---------
  mode        keyboard | leader      (default: keyboard)
  leader_port /dev/ttyUSB0           (default; only used when mode=leader)
  gz_gui      true | false           (default: true — open Gazebo GUI)
"""

import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


# ── Helper: resolve package paths at launch-time ────────────────────────────

def _pkg(pkg: str) -> str:
    return get_package_share_directory(pkg)


# ── World and model paths ────────────────────────────────────────────────────

WORLD_SDF  = os.path.join(_pkg('turtle_gazebo'), 'worlds',  'arm_lab.sdf')
MODEL_PATH = os.path.join(_pkg('turtle_gazebo'), 'models')   # parent dir for GZ_SIM_RESOURCE_PATH


def generate_launch_description():

    # ── Declare arguments ───────────────────────────────────────────────────
    declare_mode = DeclareLaunchArgument(
        'mode',
        default_value='keyboard',
        description='Control mode: keyboard | leader',
    )

    declare_port = DeclareLaunchArgument(
        'leader_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for leader arm (used when mode=leader)',
    )

    declare_gui = DeclareLaunchArgument(
        'gz_gui',
        default_value='true',
        description='Open Gazebo GUI (true/false)',
    )

    mode        = LaunchConfiguration('mode')
    leader_port = LaunchConfiguration('leader_port')
    gz_gui      = LaunchConfiguration('gz_gui')

    # ── 1. Gazebo Sim ───────────────────────────────────────────────────────
    # Set GZ_SIM_RESOURCE_PATH so Gazebo can find the so101_arm model directory
    env = dict(os.environ)
    existing = env.get('GZ_SIM_RESOURCE_PATH', '')
    env['GZ_SIM_RESOURCE_PATH'] = (
        MODEL_PATH + ':' + existing if existing else MODEL_PATH
    )

    gz_sim = ExecuteProcess(
        cmd=[
            FindExecutable(name='gz'),
            'sim',
            WORLD_SDF,
            # '--headless-rendering' is omitted — added only when gz_gui is false below
        ],
        additional_env=env,
        output='screen',
        condition=IfCondition(gz_gui),
    )

    gz_sim_headless = ExecuteProcess(
        cmd=[
            FindExecutable(name='gz'),
            'sim',
            '--headless-rendering',
            '-s',                         # server only
            WORLD_SDF,
        ],
        additional_env=env,
        output='screen',
        condition=UnlessCondition(gz_gui),
    )

    # ── 2. ros_gz_bridge — joint commands + joint states ───────────────────
    #    Bridge converts ROS std_msgs/Float64 → Gazebo gz.msgs.Double on
    #    each /so101/<joint> topic, and publishes /so101/joint_states back.
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='arm_gz_bridge',
        output='screen',
        arguments=[
            # Joint command topics (ROS → Gz)
            '/so101/shoulder_pan@std_msgs/msg/Float64@gz.msgs.Double',
            '/so101/shoulder_lift@std_msgs/msg/Float64@gz.msgs.Double',
            '/so101/elbow_flex@std_msgs/msg/Float64@gz.msgs.Double',
            '/so101/wrist_flex@std_msgs/msg/Float64@gz.msgs.Double',
            '/so101/wrist_roll@std_msgs/msg/Float64@gz.msgs.Double',
            '/so101/gripper@std_msgs/msg/Float64@gz.msgs.Double',
            # Joint states (Gz → ROS)
            '/so101/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            # World clock
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
    )

    # ── 3. Spawn SO-101 arm in the running simulation ──────────────────────
    #    Wait 4 s for Gazebo to finish loading before spawning.
    spawn_arm = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                name='spawn_so101',
                output='screen',
                arguments=[
                    '-world', 'arm_lab',
                    '-file', os.path.join(MODEL_PATH, 'so101_arm', 'model.sdf'),
                    '-name', 'so101_arm',
                    # Base at x=1.0 y=0 z=0.72 (on the table surface)
                    '-x', '1.0',
                    '-y', '0.0',
                    '-z', '0.72',
                ],
            ),
        ],
    )

    # ── 4a. Keyboard control ────────────────────────────────────────────────
    keyboard_node = TimerAction(
        period=5.0,   # give the bridge time to come up first
        actions=[
            Node(
                package='turtle_control',
                executable='arm_keyboard_teleop',
                name='arm_keyboard_teleop',
                output='screen',
                prefix='xterm ' ',         # open in its own terminal so it gets stdin
                condition=IfCondition(
                    PythonExpression(["'", mode, "' == 'keyboard'"])
                ),
            ),
        ],
    )

    # ── 4b. Leader arm bridge ───────────────────────────────────────────────
    leader_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='turtle_control',
                executable='leader_bridge',
                name='leader_bridge',
                output='screen',
                parameters=[{'port': leader_port}],
                condition=IfCondition(
                    PythonExpression(["'", mode, "' == 'leader'"])
                ),
            ),
        ],
    )

    return LaunchDescription([
        declare_mode,
        declare_port,
        declare_gui,
        gz_sim,
        gz_sim_headless,
        ros_gz_bridge,
        spawn_arm,
        keyboard_node,
        leader_node,
    ])

