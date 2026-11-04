"""
sim_teleop.launch.py — TURTLE Robotics SI
==========================================
All-in-one launcher for the SO-101 Gazebo sim + teleop + recorder.

Modes
-----
  keyboard  (default, at-home)
    ros2 launch turtle_gazebo sim_teleop.launch.py

  leader    (in-lab, physical leader arm)
    ros2 launch turtle_gazebo sim_teleop.launch.py mode:=leader port:=/dev/ttyACM1
"""

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, LaunchConfigurationEquals
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    declare_mode = DeclareLaunchArgument(
        "mode", default_value="keyboard",
        description="Teleop mode: keyboard (at-home) or leader (in-lab)",
    )
    declare_port = DeclareLaunchArgument(
        "port", default_value="/dev/ttyACM1",
        description="USB port for the leader arm (leader mode only)",
    )
    declare_robot_id = DeclareLaunchArgument(
        "robot_id", default_value="so_leader",
        description="lerobot robot_id for the leader arm",
    )
    declare_output_dir = DeclareLaunchArgument(
        "output_dir", default_value="~/sim_dataset",
        description="Directory to save recorded episodes",
    )
    declare_num_episodes = DeclareLaunchArgument(
        "num_episodes", default_value="50",
        description="Number of episodes to record",
    )
    declare_episode_time = DeclareLaunchArgument(
        "episode_time_s", default_value="30",
        description="Maximum duration of each episode in seconds",
    )
    declare_record = DeclareLaunchArgument(
        "record", default_value="true",
        description="Whether to launch the sim_recorder node",
    )

    gazebo_launch_dir = get_package_share_directory("turtle_gazebo")
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_launch_dir, "launch", "simulation_with_arm.launch.py")
        )
    )

    keyboard_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="turtle_control",
                executable="keyboard_teleop",
                name="keyboard_teleop",
                output="screen",
                prefix="xterm -e",
                condition=LaunchConfigurationEquals("mode", "keyboard"),
            )
        ],
    )

    leader_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="turtle_control",
                executable="leader_bridge",
                name="leader_bridge",
                output="screen",
                parameters=[
                    {"port":     LaunchConfiguration("port")},
                    {"robot_id": LaunchConfiguration("robot_id")},
                ],
                condition=LaunchConfigurationEquals("mode", "leader"),
            )
        ],
    )

    recorder_node = TimerAction(
        period=6.0,
        actions=[
            Node(
                package="turtle_control",
                executable="sim_recorder",
                name="sim_recorder",
                output="screen",
                prefix="xterm -e",
                parameters=[
                    {"output_dir":    LaunchConfiguration("output_dir")},
                    {"num_episodes":  LaunchConfiguration("num_episodes")},
                    {"episode_time_s": LaunchConfiguration("episode_time_s")},
                ],
                condition=IfCondition(LaunchConfiguration("record")),
            )
        ],
    )

    return LaunchDescription([
        declare_mode, declare_port, declare_robot_id,
        declare_output_dir, declare_num_episodes,
        declare_episode_time, declare_record,
        sim_launch, keyboard_node, leader_node, recorder_node,
    ])
