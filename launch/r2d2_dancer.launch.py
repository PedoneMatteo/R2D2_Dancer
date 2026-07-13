"""
r2d2_dancer.launch.py - Avvia tutto l'ecosistema per R2D2 danzante
=================================================================

Questo launch file avvia TRE cose contemporaneamente:

1. state_publisher (il nostro nodo Python)
   → pubblica /joint_states con gli angoli animati

2. robot_state_publisher (nodo standard ROS2)
   → legge il file URDF e lo pubblica su /robot_description
   → riceve /joint_states
   → calcola e pubblica la struttura TF su /tf

3. rviz2 (visualizzatore 3D)
   → si connette a /tf e /robot_description
   → disegna R2D2 in 3D e lo vedi ballare!

COME USARLO:
  ros2 launch r2d2_dancer r2d2_dancer.launch.py

In RViz, se non vedi R2D2:
- Aggiungi un display "RobotModel" dal pannello "Add" (in basso a sinistra)
- Assicurati che "Fixed Frame" (pannello "Global Options") sia "base_link"
- Aggiungi un display "TF" per vedere i sistemi di riferimento (assi colorati)

MODIFICHE:
- Per usare un URDF diverso, cambia il percorso in os.path.join()
- Per non aprire RViz automaticamente, commenta o rimuovi il Node rviz2
- Per aggiungere altri nodi, aggiungi altri Node(...) alla LaunchDescription
"""

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    """
    Questa funzione viene chiamata da ros2 launch.
    Restituisce una LaunchDescription: la lista di processi da avviare.
    """

    # ─── Percorso del file URDF ────────────────────────────────
    # Trova automaticamente la directory del pacchetto
    pkg_dir = get_package_share_directory('r2d2_dancer')
    urdf_path = os.path.join(pkg_dir, 'urdf', 'r2d2.urdf')

    # Legge il contenuto del file URDF come stringa.
    # robot_state_publisher se lo aspetta così (non come path!).
    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    # ─── 1. Nodo state_publisher (il nostro!) ──────────────────
    state_pub = Node(
        package='r2d2_dancer',
        executable='state_publisher',  # definito in setup.py
        name='state_publisher',
        output='screen',  # stampa i log nel terminale
    )

    # ─── 2. Nodo robot_state_publisher (di sistema) ────────────
    # Questo nodo è parte del pacchetto "robot_state_publisher".
    # Legge l'URDF + i JointState → produce la TF tree.
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            # Passa l'URDF come parametro.
            # Il nome del parametro DEVE essere 'robot_description'.
            'robot_description': robot_description,
        }],
    )

    # ─── 3. RViz (visualizzatore 3D) ───────────────────────────
    # Avvia rviz2 con il file di configurazione pre-impostato.
    # RobotModel, TF e Fixed Frame sono già configurati.
    rviz_config = os.path.join(pkg_dir, 'rviz', 'r2d2.rviz')
    rviz = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen',
    )

    # ─── Assembla e restituisci ─────────────────────────────────
    return LaunchDescription([
        state_pub,
        robot_state_pub,
        rviz,
    ])
