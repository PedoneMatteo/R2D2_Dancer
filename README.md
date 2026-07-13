# R2D2 Danzante

[![ROS2](https://img.shields.io/badge/ROS2-Humble-brightgreen)](https://docs.ros.org/en/humble/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

Esempio didattico ROS2 che mostra come animare un robot in RViz usando **URDF**, **JointState**, **robot_state_publisher** e **TF**.

Scritto per chi inizia da zero: ogni file è pieno di commenti in italiano che spiegano ogni concetto passo passo.

### Ballo sul posto

![Ballo sul posto](video/r2d2_dancer.gif)

### Camminata in cerchio

![Camminata in cerchio](video/r2d2_walker.gif)

> Per registrare i tuoi video: leggi [video/README.md](video/README.md)

---

## Indice

- [Prerequisiti](#prerequisiti)
- [Installazione](#installazione)
- [Utilizzo](#utilizzo)
- [Cosa vedrai](#cosa-vedrai)
- [Come funziona](#come-funziona)
- [Struttura del pacchetto](#struttura-del-pacchetto)
- [Sperimentare](#sperimentare)
- [Risoluzione problemi](#risoluzione-problemi)
- [Licenza](#licenza)

---

## Prerequisiti

- **ROS2 Humble** (o successivo) installato. [Guida ufficiale](https://docs.ros.org/en/humble/Installation.html)
- **RViz2** (incluso nell'installazione desktop di ROS2)
- **colcon** per compilare il workspace

```bash
# Verifica che ROS2 sia attivo
ros2 --version
```

---

## Installazione

```bash
# 1. Vai nel tuo workspace ROS2
cd ~/ros2_ws/src

# 2. Clona il repository
git clone https://github.com/TUO-UTENTE/r2d2_dancer.git

# 3. Torna nella root del workspace e compila
cd ~/ros2_ws
colcon build --packages-select r2d2_dancer --symlink-install

# 4. Sorga l'ambiente
source install/setup.bash
```

> **Nota:** L'opzione `--symlink-install` evita di dover ricompilare dopo modifiche ai file Python e URDF.

---

## Utilizzo

### Balla sul posto (default)

```bash
ros2 launch r2d2_dancer r2d2_dancer.launch.py
```

RViz si apre **gia configurato** con RobotModel, TF e Fixed Frame su `base_link`.
R2D2 balla al centro dello schermo senza spostarsi.

### Cammina in cerchio

```bash
ros2 launch r2d2_dancer r2d2_walker.launch.py
```

RViz si apre con Fixed Frame su `world`. R2D2 percorre un cerchio di raggio 1.5m
mentre continua a ballare — la griglia resta fissa e vedi il robot muoversi nello spazio.

Per fermare: `Ctrl+C` nel terminale.

---

## Cosa vedrai

Il robot R2D2 e composto da:

| Parte       | Descrizione                                     | Movimento                    |
|-------------|-------------------------------------------------|------------------------------|
| Testa       | Cupola argentata con occhio blu e antenna rossa | Rotazione sinistra/destra    |
| Corpo       | Cilindro bianco                                 | Fermo (ancorato a base_link) |
| Braccio SX  | Parallelepipedo argentato, orizzontale          | Oscillazione su/giu          |
| Braccio DX  | Parallelepipedo argentato, orizzontale          | Oscillazione su/giu (controfase) |
| Gamba SX    | Cilindro bianco + piedino blu                   | Oscillazione avanti/indietro |
| Gamba DX    | Cilindro bianco + piedino blu                   | Oscillazione avanti/indietro (controfase) |

Le gambe sono in **controfase** (una va avanti mentre l'altra va indietro) — l'effetto e quello di un ballerino che si muove a ritmo.

---

## Come funziona

Il flusso e basato sul pattern **publish/subscribe** di ROS2 e coinvolge 3 nodi:

```
 ┌─────────────────────┐      ┌──────────────────────────────┐      ┌──────────────┐
 │  state_publisher    │      │   robot_state_publisher      │      │    RViz      │
 │                     │      │                              │      │              │
 │  PUBLISH su:        │      │  SUBSCRIBE a:                │      │ SUBSCRIBE a: │
 │  /joint_states      │─────►│  /joint_states               │      │ /tf          │
 │  (JointState msg)   │      │                              │─────►│ /robot_desc  │
 │                     │      │  Legge parametro:            │      │              │
 │  Contiene:          │      │  /robot_description (URDF)   │      │ Mostra il    │
 │  - nomi giunti      │      │                              │      │ robot in 3D  │
 │  - angoli (rad)     │      │  PUBLISH su:                 │      │ usando la TF │
 │                     │      │  /tf (transform tree)        │      │              │
 └─────────────────────┘      │  /tf_static                  │      └──────────────┘
                              │                              │
                              │  Combina URDF + JointState:  │
                              │  calcola cinematica diretta  │
                              │  e produce le trasformate    │
                              │  tra tutti i link.           │
                              └──────────────────────────────┘
```

### Dettaglio dei 3 attori

#### 1. `state_publisher.py` — Il "coreografo" (Publisher)
- Pubblica sul topic `/joint_states` messaggi di tipo `sensor_msgs/JointState`
- Ogni messaggio contiene:
  - `header.stamp`: timestamp (quando e stato calcolato questo stato)
  - `name[]`: lista dei nomi dei giunti (devono **combaciare esattamente** con quelli nell'URDF)
  - `position[]`: lista degli angoli corrispondenti, in radianti
- Gli angoli sono calcolati con `sin()` e `cos()` per creare oscillazioni fluide
- Le gambe sono in controfase (una avanti, l'altra indietro) per l'effetto "danza"

#### 2. `robot_state_publisher` — Il "calcolatore" (Subscriber + Publisher)
- E un nodo standard di ROS2 (pacchetto `robot_state_publisher`)
- **Subscriber**: si sottoscrive a `/joint_states` per ricevere gli angoli
- **Parametro**: legge `robot_description` (il contenuto del file URDF)
- **Elaborazione**: per ogni JointState ricevuto:
  1. Prende l'URDF (la struttura ad albero dei link e joint)
  2. Applica gli angoli ricevuti ai giunti corrispondenti
  3. Calcola la **cinematica diretta** (forward kinematics): partendo da `base_link`, per ogni joint calcola la trasformata (traslazione + rotazione) del link figlio rispetto al padre
  4. Produce un albero di trasformate (TF tree) che dice dove si trova ogni link nello spazio
- **Publisher**: pubblica le trasformate su `/tf` e `/tf_static`

#### 3. `RViz` — Il "visualizzatore" (Subscriber)
- Si sottoscrive a `/tf` per sapere la posa di ogni link
- Si sottoscrive a `/robot_description` per conoscere la geometria (forme, dimensioni, colori)
- Con TF + URDF, sa esattamente dove e come disegnare ogni pezzo del robot in 3D

### Perche `robot_state_publisher` e indispensabile?

Senza `robot_state_publisher`, `state_publisher` pubblicherebbe angoli "nel vuoto":
nessuno li ascolterebbe e RViz non saprebbe come tradurre un angolo in una posizione 3D.

E il subscriber intermedio che fa da ponte tra **dati astratti** (angoli) e **rappresentazione spaziale** (coordinate 3D di ogni link).

### Come funziona la camminata (modalita walker)

Per far camminare R2D2 senza Gazebo, aggiungiamo un frame `world` sopra `base_link`
e lo facciamo muovere. Il trucco e tutto nella **catena TF**:

```
world ──(TF animata da base_mover)──► base_link ──(TF da URDF)──► body, head, legs...
│                                      │
│  x = radius * cos(angle)             │  robot_state_publisher
│  y = radius * sin(angle)             │  calcola queste TF
│  yaw = angle + π/2                   │  a partire dai JointState
│                                      │
└─ base_mover pubblica questa TF ─────┘
```

**base_mover** e un quarto nodo (in `base_mover.py`) che:
- Pubblica una `TransformStamped` su `/tf` con `frame_id=world` e `child_frame_id=base_link`
- La posizione segue un cerchio: `x = radius * cos(angle)`, `y = radius * sin(angle)`
- L'orientamento (yaw) punta sempre nella direzione del moto
- `robot_state_publisher` continua a pubblicare le TF tra i link (body, head, gambe...)
- RViz, con Fixed Frame = `world`, vede tutto l'albero TF e mostra R2D2 che si muove

Il risultato e un'illusione di camminata: niente fisica reale (niente attrito, gravita,
contatti), ma visivamente credibile e perfetta per imparare come funziona TF.

---

## Struttura del pacchetto

```
r2d2_dancer/
├── README.md                          ← Questo file
├── LICENSE                            ← Licenza MIT
├── setup.py                           ← Entry point e installazione
├── package.xml                        ← Dipendenze ROS2
├── .gitignore
├── r2d2_dancer/
│   ├── __init__.py
│   ├── state_publisher.py             ← Il nodo "coreografo" (ballo sul posto)
│   └── base_mover.py                  ← Il nodo "camminatore" (sposta base_link)
├── urdf/
│   └── r2d2.urdf                      ← Modello 3D del robot
├── launch/
│   ├── r2d2_dancer.launch.py          ← Launch: ballo sul posto
│   └── r2d2_walker.launch.py          ← Launch: ballo + camminata in cerchio
├── rviz/
│   ├── r2d2.rviz                      ← Config RViz (Fixed Frame: base_link)
│   └── r2d2_walker.rviz               ← Config RViz (Fixed Frame: world)
├── video/
│   ├── README.md                      ← Istruzioni per registrare i video
│   ├── r2d2_dancer.gif                ← Demo: ballo sul posto
│   └── r2d2_walker.gif                ← Demo: camminata in cerchio
└── resource/
    └── r2d2_dancer
```

---

## Sperimentare

Il bello di questo esempio e che puoi modificarlo facilmente:

### Cambiare la velocita della danza
In `r2d2_dancer/state_publisher.py`, modifica l'incremento dell'angolo:

```python
self.angle += 0.1   # originale: 20 Hz, 2 rad/s
self.angle += 0.2   # doppia velocita
self.angle += 0.05  # meta velocita
```

### Aggiungere nuove parti al robot
1. **URDF**: aggiungi un nuovo `<link>` e uno `<joint>`
2. **state_publisher.py**: aggiungi il nome del joint all'array `joint_state.name` e calcola la sua posizione

### Cambiare i colori
Nel file `urdf/r2d2.urdf`, modifica i valori RGBA nei `<material>`:
```xml
<material name="r2d2_blue">
    <color rgba="0.1 0.3 0.8 1.0"/>   <!-- R  G  B  Alpha (0.0–1.0) -->
</material>
```

### Aggiungere un pattern di movimento diverso
Prova funzioni alternative in `timer_callback()`:
```python
# Movimento a scatto (dente di sega)
pos = (self.angle % 1.0) * 1.2 - 0.6

# Movimento casuale smooth
import random
pos += (random.random() - 0.5) * 0.1
pos = max(-0.6, min(0.6, pos))
```

### Modificare il percorso della camminata
In `r2d2_dancer/base_mover.py`, cambia il pattern di movimento:
```python
# Cerchio piu grande
self.radius = 3.0

# Linea retta (toglie sin/cos)
t.transform.translation.x = self.angle * 0.5  # avanza lungo X
t.transform.translation.y = 0.0

# Spirale (raggio cresce nel tempo)
r = 0.5 + self.angle * 0.1
t.transform.translation.x = r * cos(self.angle)
t.transform.translation.y = r * sin(self.angle)
```

---

## Risoluzione problemi

| Problema | Soluzione |
|----------|-----------|
| RViz non mostra nulla | Apri il launch con la config (`-d rviz/r2d2.rviz`). In alternativa aggiungi manualmente "RobotModel" e imposta Fixed Frame su `base_link`. |
| Il robot e fermo | Verifica che `state_publisher` sia in esecuzione: `ros2 node list`. Se manca, controlla i log. |
| I pezzi sono scollegati | I nomi dei giunti in `state_publisher.py` devono **combaciare esattamente** con quelli nell'URDF (case-sensitive!). |
| RViz crasha / rallenta | Se hai una GPU integrata, prova a ridurre il rate del timer in `state_publisher.py` (es. `0.1` invece di `0.05`). |
| `colcon build` fallisce | Assicurati che tutte le dipendenze siano installate: `sudo apt install ros-humble-robot-state-publisher ros-humble-rviz2` |

---

## Licenza

MIT — vedi il file [LICENSE](LICENSE) per i dettagli.

---

*Creato come esempio didattico per imparare ROS2, URDF, JointState e TF. Perfetto per studenti e principianti.*
