"""
base_mover.py - Makes R2D2 "walk" in space
==================================================

This node publishes an animated TF from 'world' to 'base_link'.
Before, base_link was the root of the TF tree and stood still at the center.
Now we introduce a 'world' frame above, which acts as a "fixed world".

The effect is that R2D2 moves through space while continuing to dance:
the legs swing, and the body follows a path (circle, straight, etc).

HOW IT WORKS:
==============

    world ──(TF: x=cos, y=sin, yaw=rot)──► base_link
                                                │
                                          all of R2D2
                                          (legs, head, arms...)

   base_mover           robot_state_publisher          RViz
   (this node)          (TF from URDF + JointState)    (Fixed Frame: world)
       │                         │                         │
       │  /tf: world→base_link   │  /tf: base_link→body   │
       │                         │        body→head       │
       │ ──────────────────────► │        body→legs...    │
       │                         │ ────────────────────►  │  You see R2D2
       │                         │                        │  moving!

IMPORTANT NOTE:
- robot_state_publisher publishes ALL TFs (body, head, legs...)
  including world→base_link? NO. It only publishes TFs between links
  defined in the URDF. The world→base_link TF must come from US.
- That's why we need this separate node.
- Frames without a parent become "orphans": robot_state_publisher
  does not know where to attach base_link, so it does not publish that TF.
  base_mover provides the missing "hook".

CREATIVE MODIFICATIONS:
- Change the movement pattern: straight line, spiral, zig-zag...
- Sync the speed with the frequency of the legs
- Use /cmd_vel to control the movement via keyboard/joystick
"""

from math import pi, sin, cos

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class BaseMover(Node):
    """
    Node that publishes the animated TF world → base_link.

    Makes R2D2 move along a circular path while
    orienting it in the direction of motion (tangent to the circle).
    """

    def __init__(self):
        super().__init__('base_mover')

        # ─── TF Broadcaster ────────────────────────────────────
        # TransformBroadcaster is the standard way to publish
        # TF transforms in ROS2. Internally it publishes on the /tf topic.
        self.tf_broadcaster = TransformBroadcaster(self)

        # ─── Timer ──────────────────────────────────────────────
        # Same frequency as state_publisher (20 Hz) to
        # keep the movement smooth and synchronized.
        self.timer = self.create_timer(0.05, self.timer_callback)

        # ─── Movement parameters ───────────────────────────────
        self.angle = 0.0          # animation "time" (rad)
        self.radius = 1.5         # circle radius (meters)

        self.get_logger().info(
            'BaseMover started! R2D2 will walk in a circle '
            f'(radius={self.radius}m).'
        )
        self.get_logger().info(
            'In RViz, set Fixed Frame to "world" to see '
            'R2D2 moving.'
        )

    def timer_callback(self):
        """
        Computes the position of base_link in the world and publishes the TF.
        Called 20 times per second.
        """
        # ─── Position on the circle ───────────────────────────────
        # x = radius * cos(angle): projection on the X axis
        # y = radius * sin(angle): projection on the Y axis
        x = self.radius * cos(self.angle)
        y = self.radius * sin(self.angle)

        # ─── Orientation ────────────────────────────────────────
        # R2D2 must face the direction of motion.
        # On a counterclockwise circle, the tangent is
        # perpendicular to the radius. For a circle:
        #   position = (cos(θ), sin(θ))
        #   tangent  = (-sin(θ), cos(θ))
        # The angle of the tangent (relative to +X) is:
        #   yaw = θ + π/2
        # Why? Because at θ=0 (point (r,0)), the tangent points
        # towards +Y (up), which is 90° (π/2).
        yaw = self.angle + pi / 2

        # ─── Build the TransformStamped message ────────────
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'world'       # parent frame (fixed)
        t.child_frame_id = 'base_link'    # child frame (moving)

        # Translation: where base_link is in the world
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = 0.0  # on the floor

        # Rotation: yaw around Z (the robot faces forward)
        # We use a quaternion. tf2 provides helpers, but here
        # we compute it manually from the yaw.
        # q = (qx, qy, qz, qw) = (0, 0, sin(yaw/2), cos(yaw/2))
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = sin(yaw / 2.0)
        t.transform.rotation.w = cos(yaw / 2.0)

        # ─── Publish ────────────────────────────────────────────
        self.tf_broadcaster.sendTransform(t)

        # ─── Advance the animation ─────────────────────────────────
        # Slower increment than the legs for a
        # believable walking movement (linear speed ≈ 0.075 m/s
        # at the periphery of a 1.5m radius circle).
        self.angle += 0.05

        # Keep the angle in [0, 2π) to avoid overflow
        # (though floats don't overflow easily)
        if self.angle > 2 * pi:
            self.angle -= 2 * pi


def main(args=None):
    rclpy.init(args=args)
    node = BaseMover()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
