"""
base_mover.py - Fa "camminare" R2D2 nello spazio
==================================================

Questo nodo pubblica una TF animata da 'world' a 'base_link'.
Prima, base_link era la radice dell'albero TF e stava fermo al centro.
Ora introduciamo un frame 'world' sopra, che fa da "mondo fisso".

L'effetto e che R2D2 si sposta nello spazio mentre continua a ballare:
le gambe oscillano, e il corpo segue un percorso (cerchio, dritto, etc).

COME FUNZIONA:
==============

    world ──(TF: x=cos, y=sin, yaw=rot)──► base_link
                                                │
                                          tutto R2D2
                                          (gambe, testa, braccia...)

   base_mover           robot_state_publisher          RViz
   (questo nodo)        (TF da URDF + JointState)      (Fixed Frame: world)
       │                         │                         │
       │  /tf: world→base_link   │  /tf: base_link→body   │
       │                         │        body→head       │
       │ ──────────────────────► │        body→legs...    │
       │                         │ ────────────────────►  │  Vedi R2D2
       │                         │                        │  muoversi!

NOTA IMPORTANTE:
- robot_state_publisher pubblica TUTTE le TF (body, head, gambe...)
  incluso world→base_link? NO. Lui pubblica solo le TF tra i link
  definiti nell'URDF. La TF world→base_link deve venire da NOI.
- Per questo abbiamo bisogno di questo nodo separato.
- I frame senza parent diventano "orfani": robot_state_publisher
  non sa dove attaccare base_link, quindi non pubblica quella TF.
  base_mover fornisce il "gancio" mancante.

MODIFICHE CREATIVE:
- Cambia il pattern di movimento: linea retta, spirale, zig-zag...
- Sincronizza la velocita con la frequenza delle gambe
- Usa /cmd_vel per controllare il movimento da tastiera/joystick
"""

from math import pi, sin, cos

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class BaseMover(Node):
    """
    Nodo che pubblica la TF animata world → base_link.

    Fa muovere R2D2 lungo un percorso circolare mentre
    lo orienta nella direzione del moto (tangente al cerchio).
    """

    def __init__(self):
        super().__init__('base_mover')

        # ─── TF Broadcaster ────────────────────────────────────
        # TransformBroadcaster e il modo standard per pubblicare
        # trasformate TF in ROS2. Internamente pubblica sul topic /tf.
        self.tf_broadcaster = TransformBroadcaster(self)

        # ─── Timer ──────────────────────────────────────────────
        # Stessa frequenza di state_publisher (20 Hz) per
        # mantenere il movimento fluido e sincronizzato.
        self.timer = self.create_timer(0.05, self.timer_callback)

        # ─── Parametri del movimento ─────────────────────────────
        self.angle = 0.0          # "tempo" dell'animazione (rad)
        self.radius = 1.5         # raggio del cerchio (metri)

        self.get_logger().info(
            'BaseMover avviato! R2D2 camminera in cerchio '
            f'(raggio={self.radius}m).'
        )
        self.get_logger().info(
            'In RViz, imposta Fixed Frame su "world" per vedere '
            'R2D2 muoversi.'
        )

    def timer_callback(self):
        """
        Calcola la posizione di base_link nel mondo e pubblica la TF.
        Chiamata 20 volte al secondo.
        """
        # ─── Posizione sul cerchio ───────────────────────────────
        # x = radius * cos(angle): proiezione sull'asse X
        # y = radius * sin(angle): proiezione sull'asse Y
        x = self.radius * cos(self.angle)
        y = self.radius * sin(self.angle)

        # ─── Orientamento ────────────────────────────────────────
        # R2D2 deve guardare nella direzione del moto.
        # Su un cerchio in senso antiorario, la tangente e
        # perpendicolare al raggio. Per un cerchio:
        #   posizione = (cos(θ), sin(θ))
        #   tangente  = (-sin(θ), cos(θ))
        # L'angolo della tangente (rispetto a +X) e:
        #   yaw = θ + π/2
        # Perche? Perche a θ=0 (punto (r,0)), la tangente punta
        # verso +Y (su), che e 90° (π/2).
        yaw = self.angle + pi / 2

        # ─── Costruisci il messaggio TransformStamped ────────────
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'world'       # frame padre (fisso)
        t.child_frame_id = 'base_link'    # frame figlio (si muove)

        # Traslazione: dove sta base_link nel mondo
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = 0.0  # sul pavimento

        # Rotazione: yaw attorno a Z (il robot guarda in avanti)
        # Usiamo un quaternione. tf2 fornisce helper, ma qui
        # calcoliamo a mano dal yaw.
        # q = (qx, qy, qz, qw) = (0, 0, sin(yaw/2), cos(yaw/2))
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = sin(yaw / 2.0)
        t.transform.rotation.w = cos(yaw / 2.0)

        # ─── Pubblica ────────────────────────────────────────────
        self.tf_broadcaster.sendTransform(t)

        # ─── Avanza l'animazione ─────────────────────────────────
        # Incremento piu lento delle gambe per un movimento
        # di camminata credibile (velocita lineare ≈ 0.075 m/s
        # alla periferia del cerchio di raggio 1.5m).
        self.angle += 0.05

        # Tieni l'angolo in [0, 2π) per evitare overflow
        # (anche se float non overflowano facilmente)
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
