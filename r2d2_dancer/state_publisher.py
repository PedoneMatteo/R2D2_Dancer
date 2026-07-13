"""
state_publisher.py - R2D2's "choreographer"
=============================================

This node periodically publishes the joint states
of the R2D2 robot. Joint values are calculated with
trigonometric functions (sin, cos), creating smooth oscillatory movements.

HOW THE ARCHITECTURE WORKS:
==============================

   state_publisher           robot_state_publisher           RViz
   (this node)               (standard ROS2 package)          (visualizer)
       │                           │                            │
       │  Publishes:               │  Subscribes to:            │
       │  /joint_states            │  /joint_states             │
       │  (JointState msg)         │                            │
       │ ──────────────────────►   │  + URDF in /robot_descrip. │
       │                           │                            │
       │                           │  Computes TF tree          │
       │                           │  Publishes: /tf            │
       │                           │ ──────────────────────────►│  Renders robot
       │                           │                            │  in 3D

KEY CONCEPTS:
- JointState: standard ROS2 message (sensor_msgs/JointState)
  Contains: header (timestamp), name[] (joint names), position[] (angles)
- Joint names in JointState MUST EXACTLY match
  the joint names in the URDF file
- robot_state_publisher is a ready-made ROS2 node that:
  1. Reads the URDF (robot structure)
  2. Receives JointState (joint angles)
  3. Computes forward kinematics (position of each link)
  4. Publishes the TF structure (transform tree) on /tf
- RViz reads /tf and /robot_description and draws the robot in 3D

CREATIVE MODIFICATIONS:
- Change frequencies by multiplying self.angle by different values
- Use different functions: sawtooth wave, random...
- Add more joints (modify URDF + add names here)
- Synchronize movements with music (e.g., audio analysis)
"""

import math
from math import pi, sin, cos

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class StatePublisher(Node):
    """
    Node that animates R2D2 by publishing JointState at 20 Hz (every 0.05 seconds).

    Each joint receives a position calculated with sin/cos, creating
    smooth oscillations. Different joints have different phases to
    create a coordinated "dance" effect.
    """

    def __init__(self):
        # Initialize the node with name 'state_publisher'
        super().__init__('state_publisher')

        # ─── Publishers ─────────────────────────────────────────
        # Create a publisher for the /joint_states topic.
        # - Message type: JointState (from sensor_msgs.msg)
        # - Queue size: 10 (message buffer in case of delays)
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)

        # ─── Timer ──────────────────────────────────────────────
        # Calls timer_callback() every 0.05 seconds → 20 Hz
        # 20 Hz is a good compromise: smooth for the eyes,
        # not too heavy on the CPU.
        self.timer = self.create_timer(0.05, self.timer_callback)

        # ─── Internal state ──────────────────────────────────────
        # self.angle is the "time" variable of our animation.
        # Incremented at each frame, it is used as input for sin/cos.
        # Increasing the increment (0.1 → 0.2) makes the robot dance faster.
        self.angle = 0.0

        # ─── Debug ──────────────────────────────────────────────
        self.get_logger().info('StatePublisher started!')
        self.get_logger().info(
            'The animated joints are: ' +
            'joint_head, joint_left_leg, joint_right_leg, '
            'joint_left_arm, joint_right_arm'
        )
        self.get_logger().info(
            'Open RViz and add "RobotModel" to see R2D2 dance!'
        )

    def timer_callback(self):
        """
        Called 20 times per second by the timer.
        Calculates joint positions and publishes them.

        MOVEMENT LOGIC:
        - sin(angle): oscillates between -1 and +1, period 2π (~63 steps at 0.1)
        - cos(angle): like sin but shifted by 90°
        - Multiplying by an amplitude (e.g., 0.6) limits the excursion
        - Adding an offset to the phase, each joint dances "at a different time"
        """
        # Create a new JointState message
        joint_state = JointState()

        # ─── Header ────────────────────────────────────────────
        # Every ROS message has a header with a timestamp.
        # The timestamp says "this is the robot's state at this instant".
        joint_state.header.stamp = self.get_clock().now().to_msg()

        # ─── Joint names ────────────────────────────────────
        # MUST EXACTLY match the names in the URDF file!
        # If you write "testa" here but the URDF has "joint_head",
        # robot_state_publisher will not find the match and the joint
        # will stay in its default position.
        joint_state.name = [
            'joint_head',       # Head rotation (Z axis, yaw)
            'joint_left_leg',   # Left leg oscillation (Y axis)
            'joint_right_leg',  # Right leg oscillation (Y axis)
            'joint_left_arm',   # Left arm oscillation (X axis)
            'joint_right_arm',  # Right arm oscillation (X axis)
        ]

        # ─── Joint positions ──────────────────────────────
        # Each position is an angle in RADIANS.
        #
        # THE HEAD: turns left and right slowly
        #   sin(angle * 0.7): reduced frequency (factor 0.7)
        #   * 0.8: max amplitude ±0.8 rad (±46°)
        head_pos = sin(self.angle * 0.7) * 0.8

        # LEFT LEG: swings forward/backward
        #   sin(self.angle): base oscillation
        #   * 0.6: reduced amplitude for a believable movement
        left_leg_pos = sin(self.angle) * 0.6

        # RIGHT LEG: swings in OPPOSITE PHASE to the left one
        #   -sin(self.angle): opposite sign → when one goes forward,
        #   the other goes backward (like when dancing!)
        #   This is the trick for the "dance" effect!
        right_leg_pos = -sin(self.angle) * 0.6

        # LEFT ARM: faster and asymmetric movement
        #   sin(angle * 1.3): 1.3x frequency → moves faster
        left_arm_pos = sin(self.angle * 1.3) * 0.5

        # RIGHT ARM: in opposite phase, different frequency
        #   cos is shifted by 90° relative to sin
        right_arm_pos = cos(self.angle * 1.3) * 0.5

        joint_state.position = [
            head_pos,
            left_leg_pos,
            right_leg_pos,
            left_arm_pos,
            right_arm_pos,
        ]

        # ─── Publish ──────────────────────────────────────────
        self.publisher.publish(joint_state)

        # ─── Increment the animation "time" ──────────────
        # 0.1 radians per frame @ 20 Hz = 2 rad/s ≈ 115°/s
        # To dance faster: increase (e.g., 0.15, 0.2)
        # To dance slower: decrease (e.g., 0.05, 0.03)
        # You can also use a variable increment!
        self.angle += 0.1

        # The angle grows indefinitely, but sin/cos are periodic
        # (period 2π), so there's no overflow problem for
        # reasonable sessions. If you want, you can keep it bounded:
        #   if self.angle > 2 * pi: self.angle -= 2 * pi


def main(args=None):
    """
    Node entry point. Starts the ROS2 loop.
    All Python nodes follow this pattern:
    1. rclpy.init()   → initializes the ROS2 middleware
    2. Build the node
    3. rclpy.spin()   → infinite loop that processes callbacks and timers
    4. rclpy.shutdown() → cleanup on exit
    """
    rclpy.init(args=args)
    node = StatePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
