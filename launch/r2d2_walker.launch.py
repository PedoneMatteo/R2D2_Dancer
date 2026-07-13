"""
r2d2_walker.launch.py - Avvia R2D2 che CAMMINA in cerchio
===========================================================

Differenza rispetto a r2d2_dancer.launch.py:
- Aggiunge base_mover, un nodo che pubblica la TF world → base_link
- Usa un file RViz con Fixed Frame = "world"
- R2D2 si sposta nello spazio (non balla sul posto)

COME USARLO:
  ros2 launch r2d2_dancer r2d2_walker.launch.py

In RViz vedrai R2D2 percorrere un cerchio mentre balla.
La griglia rimane fissa (ancorata a world) e il robot si muove.
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

    # ─── 1. state_publisher (le gambe ballano) ──────────────
    state_pub = Node(
        package='r2d2_dancer',
        executable='state_publisher',
        name='state_publisher',
        output='screen',
    )

    # ─── 2. base_mover (il corpo si sposta) ────────────────
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

    # ─── 4. RViz con config per walker ──────────────────────
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
