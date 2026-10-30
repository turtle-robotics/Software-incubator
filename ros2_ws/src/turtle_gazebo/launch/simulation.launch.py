"""
TURTLE Robotics SI — Gazebo Simulation Launch File
Starts Gazebo with an empty world and spawns the turtle_bot.
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

    # Start Gazebo with our empty world
    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": world_file}.items(),
    )

    # Spawn the turtle_bot model after Gazebo is up (3-second delay)
    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "ros2", "run", "ros_gz_sim", "create",
                    "-name", "turtle_bot",
                    "-file", os.path.join(
                        turtle_gazebo_share, "models", "turtle_bot", "model.sdf"
                    ),
                    "-x", "0.0",
                    "-y", "0.0",
                    "-z", "0.15",
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
    ])
