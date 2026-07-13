"""
r2d2_walker.launch.py - Starts R2D2 WALKING in a circle
===========================================================

Difference from r2d2_dancer.launch.py:
- Adds base_mover, a node that publishes the TF world → base_link
- Uses an RViz file with Fixed Frame = "world"
- R2D2 moves in space (does not dance in place)

HOW TO USE:
  ros2 launch r2d2_dancer r2d2_walker.launch.py

In RViz you will see R2D2 travel in a circle while dancing.
The grid stays fixed (anchored to world) and the robot moves.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('r2d2_dancer')
    urdf_path = os.path.join(pkg_dir, 'urdf', 'r2d2.urdf')

    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    # ─── 1. state_publisher (legs dance) ──────────────
    state_pub = Node(
        package='r2d2_dancer',
        executable='state_publisher',
        name='state_publisher',
        output='screen',
    )

    # ─── 2. base_mover (body moves) ────────────────
    base_mover = Node(
        package='r2d2_dancer',
        executable='base_mover',
        name='base_mover',
        output='screen',
    )

    # ─── 3. robot_state_publisher ────────────────────────────
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
        }],
    )

    # ─── 4. RViz with config for walker ──────────────────────
    rviz_config = os.path.join(pkg_dir, 'rviz', 'r2d2_walker.rviz')
    rviz = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen',
    )

    return LaunchDescription([
        state_pub,
        base_mover,
        robot_state_pub,
        rviz,
    ])
