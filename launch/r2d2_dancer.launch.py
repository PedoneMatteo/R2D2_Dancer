"""
r2d2_dancer.launch.py - Starts the entire ecosystem for dancing R2D2
=================================================================

This launch file starts THREE things simultaneously:

1. state_publisher (our Python node)
   → publishes /joint_states with animated angles

2. robot_state_publisher (standard ROS2 node)
   → reads the URDF file and publishes it on /robot_description
   → receives /joint_states
   → computes and publishes the TF tree on /tf

3. rviz2 (3D visualizer)
   → connects to /tf and /robot_description
   → draws R2D2 in 3D and you see it dance!

HOW TO USE:
  ros2 launch r2d2_dancer r2d2_dancer.launch.py

In RViz, if you don't see R2D2:
- Add a "RobotModel" display from the "Add" panel (bottom left)
- Make sure "Fixed Frame" ("Global Options" panel) is "base_link"
- Add a "TF" display to see the reference frames (colored axes)

CHANGES:
- To use a different URDF, change the path in os.path.join()
- To not open RViz automatically, comment or remove the rviz2 Node
- To add more nodes, add more Node(...) to the LaunchDescription
"""

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    """
    This function is called by ros2 launch.
    Returns a LaunchDescription: the list of processes to start.
    """

    # ─── Path to the URDF file ────────────────────────────────
    # Automatically finds the package directory
    pkg_dir = get_package_share_directory('r2d2_dancer')
    urdf_path = os.path.join(pkg_dir, 'urdf', 'r2d2.urdf')

    # Reads the URDF file content as a string.
    # robot_state_publisher expects it this way (not as a path!).
    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    # ─── 1. state_publisher node (ours!) ──────────────────
    state_pub = Node(
        package='r2d2_dancer',
        executable='state_publisher',  # defined in setup.py
        name='state_publisher',
        output='screen',  # prints logs to the terminal
    )

    # ─── 2. robot_state_publisher node (system) ────────────
    # This node is part of the "robot_state_publisher" package.
    # Reads the URDF + JointState → produces the TF tree.
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            # Passes the URDF as a parameter.
            # The parameter name MUST be 'robot_description'.
            'robot_description': robot_description,
        }],
    )

    # ─── 3. RViz (3D visualizer) ───────────────────────────
    # Starts rviz2 with the pre-set configuration file.
    # RobotModel, TF and Fixed Frame are already configured.
    rviz_config = os.path.join(pkg_dir, 'rviz', 'r2d2.rviz')
    rviz = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen',
    )

    # ─── Assemble and return ─────────────────────────────────
    return LaunchDescription([
        state_pub,
        robot_state_pub,
        rviz,
    ])
