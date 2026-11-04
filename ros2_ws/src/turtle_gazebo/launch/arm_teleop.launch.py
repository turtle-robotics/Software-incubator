import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_gz   = get_package_share_directory('turtle_gazebo')
    world    = os.path.join(pkg_gz, 'worlds', 'arm_lab.sdf')
    model_dir = os.path.join(pkg_gz, 'models')

    env = dict(os.environ)
    env['GZ_SIM_RESOURCE_PATH'] = model_dir + ':' + env.get('GZ_SIM_RESOURCE_PATH', '')

    mode   = LaunchConfiguration('mode')
    gz_gui = LaunchConfiguration('gz_gui')

    return LaunchDescription([
        DeclareLaunchArgument('mode',   default_value='keyboard', description='keyboard | leader'),
        DeclareLaunchArgument('gz_gui', default_value='true',     description='Open Gazebo GUI'),

        ExecuteProcess(cmd=['gz', 'sim', world], additional_env=env, output='screen',
                       condition=IfCondition(gz_gui)),
        ExecuteProcess(cmd=['gz', 'sim', '--headless-rendering', '-s', world],
                       additional_env=env, output='screen', condition=UnlessCondition(gz_gui)),

        Node(package='ros_gz_bridge', executable='parameter_bridge', name='arm_gz_bridge',
             output='screen', arguments=[
                 '/so101/shoulder_pan@std_msgs/msg/Float64@gz.msgs.Double',
                 '/so101/shoulder_lift@std_msgs/msg/Float64@gz.msgs.Double',
                 '/so101/elbow_flex@std_msgs/msg/Float64@gz.msgs.Double',
                 '/so101/wrist_flex@std_msgs/msg/Float64@gz.msgs.Double',
                 '/so101/wrist_roll@std_msgs/msg/Float64@gz.msgs.Double',
                 '/so101/gripper@std_msgs/msg/Float64@gz.msgs.Double',
                 '/so101/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
                 '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
             ]),

        TimerAction(period=4.0, actions=[
            Node(package='ros_gz_sim', executable='create', name='spawn_so101', output='screen',
                 arguments=['-world', 'arm_lab',
                             '-file', os.path.join(model_dir, 'so101_arm', 'model.sdf'),
                             '-name', 'so101_arm',
                             '-x', '1.0', '-y', '0.0', '-z', '0.72']),
        ]),

        TimerAction(period=5.0, actions=[
            Node(package='turtle_control', executable='arm_keyboard_teleop',
                 name='arm_keyboard_teleop', output='screen', prefix='xterm -e',
                 condition=IfCondition(PythonExpression(["'", mode, "' == 'keyboard'"]))),
            Node(package='turtle_control', executable='leader_bridge',
                 name='leader_bridge', output='screen',
                 condition=IfCondition(PythonExpression(["'", mode, "' == 'leader'"]))),
        ]),
    ])
