"""
state_publisher.py - Il "coreografo" di R2D2
=============================================

Questo nodo pubblica periodicamente lo stato dei giunti (joint states)
del robot R2D2. I valori dei giunti sono calcolati con funzioni
trigonometriche (sin, cos), creando movimenti oscillatori fluidi.

COME FUNZIONA L'ARCHITETTURA:
==============================

   state_publisher           robot_state_publisher           RViz
   (questo nodo)             (pacchetto ROS2 standard)       (visualizzatore)
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

CONCETTI CHIAVE:
- JointState: messaggio ROS2 standard (sensor_msgs/JointState)
  Contiene: header (timestamp), name[] (nomi giunti), position[] (angoli)
- I nomi dei giunti nel JointState DEVONO corrispondere ESATTAMENTE
  ai nomi dei joint nel file URDF
- robot_state_publisher è un nodo già pronto di ROS2 che:
  1. Legge l'URDF (struttura del robot)
  2. Riceve i JointState (angoli dei giunti)
  3. Calcola la cinematica diretta (posizione di ogni link)
  4. Pubblica la struttura TF (transform tree) su /tf
- RViz legge /tf e /robot_description e disegna il robot in 3D

MODIFICHE CREATIVE:
- Cambia le frequenze moltiplicando self.angle per valori diversi
- Usa funzioni diverse: triangolare a dente di sega, random...
- Aggiungi più giunti (modifica URDF + aggiungi nomi qui)
- Sincronizza i movimenti con musica (es. analisi audio)
"""

import math
from math import pi, sin, cos

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class StatePublisher(Node):
    """
    Nodo che anima R2D2 pubblicando JointState a 20 Hz (ogni 0.05 secondi).

    Ogni giunto riceve una posizione calcolata con sin/cos, creando
    oscillazioni fluide. Giunti diversi hanno fasi diverse per
    creare un effetto di "danza" coordinata.
    """

    def __init__(self):
        # Inizializza il nodo con nome 'state_publisher'
        super().__init__('state_publisher')

        # ─── Publishers ─────────────────────────────────────────
        # Crea un publisher per il topic /joint_states.
        # - Tipo messaggio: JointState (da sensor_msgs.msg)
        # - Queue size: 10 (buffer messaggi in caso di ritardi)
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)

        # ─── Timer ──────────────────────────────────────────────
        # Chiama timer_callback() ogni 0.05 secondi → 20 Hz
        # 20 Hz è un buon compromesso: fluido per gli occhi,
        # non troppo pesante per la CPU.
        self.timer = self.create_timer(0.05, self.timer_callback)

        # ─── Stato interno ──────────────────────────────────────
        # self.angle è la variabile "tempo" della nostra animazione.
        # Incrementata ad ogni frame, viene usata come input di sin/cos.
        # Aumentando l'incremento (0.1 → 0.2) il robot balla più veloce.
        self.angle = 0.0

        # ─── Debug ──────────────────────────────────────────────
        self.get_logger().info('StatePublisher avviato!')
        self.get_logger().info(
            'I giunti animati sono: ' +
            'joint_head, joint_left_leg, joint_right_leg, '
            'joint_left_arm, joint_right_arm'
        )
        self.get_logger().info(
            'Apri RViz e aggiungi "RobotModel" per vedere R2D2 ballare!'
        )

    def timer_callback(self):
        """
        Chiamata 20 volte al secondo dal timer.
        Calcola le posizioni dei giunti e le pubblica.

        LOGICA DI MOVIMENTO:
        - sin(angle): oscilla tra -1 e +1, periodo 2π (~63 step a 0.1)
        - cos(angle): come sin ma sfasato di 90°
        - Moltiplicando per un'ampiezza (es. 0.6) limitiamo l'escursione
        - Aggiungendo offset alla fase, ogni giunto balla "a tempo diverso"
        """
        # Crea un nuovo messaggio JointState
        joint_state = JointState()

        # ─── Header ────────────────────────────────────────────
        # Ogni messaggio ROS ha un header con timestamp.
        # Il timestamp dice "questo è lo stato del robot in questo istante".
        joint_state.header.stamp = self.get_clock().now().to_msg()

        # ─── Nomi dei giunti ────────────────────────────────────
        # DEVONO corrispondere ESATTAMENTE ai nomi nel file URDF!
        # Se qui scrivi "testa" ma nell'URDF c'è "joint_head",
        # robot_state_publisher non troverà il match e il giunto
        # resterà fermo nella posizione di default.
        joint_state.name = [
            'joint_head',       # Rotazione testa (asse Z, yaw)
            'joint_left_leg',   # Oscillazione gamba sinistra (asse Y)
            'joint_right_leg',  # Oscillazione gamba destra (asse Y)
            'joint_left_arm',   # Oscillazione braccio sinistro (asse X)
            'joint_right_arm',  # Oscillazione braccio destro (asse X)
        ]

        # ─── Posizioni dei giunti ──────────────────────────────
        # Ogni posizione è un angolo in RADIANTI.
        #
        # LA TESTA: gira a sinistra e destra lentamente
        #   sin(angle * 0.7): frequenza ridotta (fattore 0.7)
        #   * 0.8: ampiezza max ±0.8 rad (±46°)
        head_pos = sin(self.angle * 0.7) * 0.8

        # GAMBA SINISTRA: oscilla avanti/indietro
        #   sin(self.angle): oscillazione base
        #   * 0.6: ampiezza ridotta per un movimento credibile
        left_leg_pos = sin(self.angle) * 0.6

        # GAMBA DESTRA: oscilla in CONTROFASE rispetto alla sinistra
        #   -sin(self.angle): segno opposto → quando una va avanti,
        #   l'altra va indietro (come quando si balla!)
        #   Questo è il trucco per l'effetto "danza"!
        right_leg_pos = -sin(self.angle) * 0.6

        # BRACCIO SINISTRO: movimento più veloce e asimmetrico
        #   sin(angle * 1.3): frequenza 1.3x → si muove più veloce
        left_arm_pos = sin(self.angle * 1.3) * 0.5

        # BRACCIO DESTRO: in controfase, frequenza diversa
        #   cos è sfasato di 90° rispetto a sin
        right_arm_pos = cos(self.angle * 1.3) * 0.5

        joint_state.position = [
            head_pos,
            left_leg_pos,
            right_leg_pos,
            left_arm_pos,
            right_arm_pos,
        ]

        # ─── Pubblica ──────────────────────────────────────────
        self.publisher.publish(joint_state)

        # ─── Incrementa il "tempo" dell'animazione ──────────────
        # 0.1 radianti per frame @ 20 Hz = 2 rad/s ≈ 115°/s
        # Per ballare più veloce: aumenta (es. 0.15, 0.2)
        # Per ballare più lento: diminuisci (es. 0.05, 0.03)
        # Puoi anche usare un incremento variabile!
        self.angle += 0.1

        # L'angolo cresce all'infinito, ma sin/cos sono periodici
        # (periodo 2π), quindi non c'è problema di overflow per
        # sessioni ragionevoli. Volendo, puoi tenerlo limitato:
        #   if self.angle > 2 * pi: self.angle -= 2 * pi


def main(args=None):
    """
    Entry point del nodo. Avvia il loop ROS2.
    Tutti i nodi Python seguono questo pattern:
    1. rclpy.init()   → inizializza il middleware ROS2
    2. Costruisci il nodo
    3. rclpy.spin()   → loop infinito che processa callback e timer
    4. rclpy.shutdown() → pulizia all'uscita
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
