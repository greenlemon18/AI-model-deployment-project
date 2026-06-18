from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='yolov5_vision',
            executable='vision_node',
            name='vision_node',
            output='screen'
        ),
        Node(
            package='motor_control',
            executable='motor_node',
            name='motor_node',
            output='screen'
        ),
    ])