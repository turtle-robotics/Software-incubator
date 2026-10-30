"""
TURTLE Robotics SI — Gazebo Simulation with SO-101 Arm
Starts Gazebo, spawns the turtle_bot AND the SO-101 arm side by side.
"""

import os
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    ExecuteProcess,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    turtle_gazebo_share = get_package_share_directory("turtle_gazebo")
    ros_gz_sim_share = get_package_share_directory("ros_gz_sim")

    world_file = os.path.join(turtle_gazebo_share, "worlds", "empty.sdf")
    turtle_bot_sdf = os.path.join(turtle_gazebo_share, "models", "turtle_bot", "model.sdf")
    arm_sdf = os.path.join(turtle_gazebo_share, "models", "so101_arm", "model.sdf")

    # Start Gazebo
    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": world_file}.items(),
    )

    # Spawn turtle_bot at the origin
    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "ros2", "run", "ros_gz_sim", "create",
                    "-name", "turtle_bot",
                    "-file", turtle_bot_sdf,
                    "-x", "0.0", "-y", "0.0", "-z", "0.15",
                ],
                output="screen",
            )
        ],
    )

    # Spawn SO-101 arm 1 m to the side (x=1.0, y=0.0)
    spawn_arm = TimerAction(
        period=4.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "ros2", "run", "ros_gz_sim", "create",
                    "-name", "so101_arm",
                    "-file", arm_sdf,
                    "-x", "1.0", "-y", "0.0", "-z", "0.0",
                ],
                output="screen",
            )
        ],
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            os.path.join(turtle_gazebo_share, "models")
            + os.pathsep
            + os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
        ),
        start_gazebo,
        spawn_robot,
        spawn_arm,
    ])
