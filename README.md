# Dancing R2D2

[![ROS2](https://img.shields.io/badge/ROS2-Humble-brightgreen)](https://docs.ros.org/en/humble/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

Educational ROS2 example showing how to animate a robot in RViz using **URDF**, **JointState**, **robot_state_publisher**, and **TF**.

Written for absolute beginners: every file is full of English comments explaining each concept step by step.

### Dancing on the spot

![Dancing on the spot](video/r2d2_dancer_nomoving.gif)

### Walking in circles

![Walking in circles](video/r2d2_dancer_moving.gif)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [What you'll see](#what-youll-see)
- [How it works](#how-it-works)
- [Package structure](#package-structure)
- [Experimenting](#experimenting)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Prerequisites

- **ROS2 Humble** (or newer) installed. [Official guide](https://docs.ros.org/en/humble/index.html)
- **RViz2** (included in the ROS2 desktop installation)
- **colcon** to build the workspace

```bash
# Verify ROS2 is active
ros2 --version
```

---

## Installation

```bash
# 1. Navigate to your ROS2 workspace
cd ~/ros2_ws/src

# 2. Clone the repository
git clone https://github.com/PedoneMatteo/R2D2_Dancer.git

# 3. Go back to the workspace root and build
cd ~/ros2_ws
colcon build --packages-select r2d2_dancer --symlink-install

# 4. Source the environment
source install/setup.bash
```

> **Note:** The `--symlink-install` option avoids having to rebuild after changes to Python and URDF files.

---

## Usage

### Dance on the spot (default)

```bash
ros2 launch r2d2_dancer r2d2_dancer.launch.py
```

RViz opens **already configured** with RobotModel, TF, and Fixed Frame set to `base_link`.
R2D2 dances in the center of the screen without moving.

### Walk in circles

```bash
ros2 launch r2d2_dancer r2d2_walker.launch.py
```

RViz opens with Fixed Frame set to `world`. R2D2 traces a circle of radius 1.5 m
while continuing to dance — the grid stays fixed and you see the robot moving through space.

To stop: `Ctrl+C` in the terminal.

---

## What you'll see

The R2D2 robot is composed of:

| Part       | Description                                     | Movement                     |
|------------|-------------------------------------------------|------------------------------|
| Head       | Silver dome with blue eye and red antenna       | Left/right rotation          |
| Body       | White cylinder                                  | Static (anchored to base_link) |
| Left arm   | Silver rectangular prism, horizontal            | Up/down oscillation          |
| Right arm  | Silver rectangular prism, horizontal            | Up/down oscillation (out of phase) |
| Left leg   | White cylinder + blue foot                      | Forward/backward oscillation |
| Right leg  | White cylinder + blue foot                      | Forward/backward oscillation (out of phase) |

The legs are **out of phase** (one moves forward while the other moves backward) — the effect is that of a dancer moving to the beat.

---

## How it works

The flow is based on the ROS2 **publish/subscribe** pattern and involves 3 nodes:

```
 ┌─────────────────────┐      ┌──────────────────────────────┐      ┌──────────────┐
 │  state_publisher    │      │   robot_state_publisher      │      │    RViz      │
 │                     │      │                              │      │              │
 │  PUBLISH on:        │      │  SUBSCRIBE to:               │      │ SUBSCRIBE to:│
 │  /joint_states      │─────►│  /joint_states               │      │ /tf          │
 │  (JointState msg)   │      │                              │─────►│ /robot_desc  │
 │                     │      │  Reads parameter:            │      │              │
 │  Contains:          │      │  /robot_description (URDF)   │      │ Shows the    │
 │  - joint names      │      │                              │      │ robot in 3D  │
 │  - angles (rad)     │      │  PUBLISH on:                 │      │ using TF     │
 │                     │      │  /tf (transform tree)        │      │              │
 └─────────────────────┘      │  /tf_static                  │      └──────────────┘
                              │                              │
                              │  Combines URDF + JointState: │
                              │  computes forward kinematics │
                              │  and produces the transforms │
                              │  between all links.          │
                              └──────────────────────────────┘
```

### The 3 actors in detail

#### 1. `state_publisher.py` — The "choreographer" (Publisher)
- Publishes `sensor_msgs/JointState` messages on the `/joint_states` topic
- Each message contains:
  - `header.stamp`: timestamp (when this state was computed)
  - `name[]`: list of joint names (must **exactly match** those in the URDF)
  - `position[]`: list of the corresponding angles, in radians
- Angles are computed using `sin()` and `cos()` to create smooth oscillations
- The legs are out of phase (one forward, the other backward) for the "dance" effect

#### 2. `robot_state_publisher` — The "calculator" (Subscriber + Publisher)
- It is a standard ROS2 node (`robot_state_publisher` package)
- **Subscriber**: subscribes to `/joint_states` to receive the angles
- **Parameter**: reads `robot_description` (the contents of the URDF file)
- **Processing**: for each JointState received:
  1. Takes the URDF (the tree structure of links and joints)
  2. Applies the received angles to the corresponding joints
  3. Computes **forward kinematics**: starting from `base_link`, for each joint it calculates the transform (translation + rotation) of the child link relative to the parent
  4. Produces a tree of transforms (TF tree) that states where each link is in space
- **Publisher**: publishes the transforms on `/tf` and `/tf_static`

#### 3. `RViz` — The "visualizer" (Subscriber)
- Subscribes to `/tf` to know the pose of each link
- Subscribes to `/robot_description` to know the geometry (shapes, dimensions, colors)
- With TF + URDF, it knows exactly where and how to draw each piece of the robot in 3D

### Why is `robot_state_publisher` indispensable?

Without `robot_state_publisher`, `state_publisher` would publish angles "into the void":
no one would listen, and RViz would not know how to translate an angle into a 3D position.

It is the intermediate subscriber that bridges **abstract data** (angles) and **spatial representation** (3D coordinates of each link).

### How the walking works (walker mode)

To make R2D2 walk without Gazebo, we add a `world` frame above `base_link`
and make it move. The trick is all in the **TF chain**:

```
world ──(TF animated by base_mover)──► base_link ──(TF from URDF)──► body, head, legs...
│                                      │
│  x = radius * cos(angle)             │  robot_state_publisher
│  y = radius * sin(angle)             │  computes these TFs
│  yaw = angle + π/2                   │  from the JointState
│                                      │
└─ base_mover publishes this TF ───────┘
```

**base_mover** is a fourth node (in `base_mover.py`) that:
- Publishes a `TransformStamped` on `/tf` with `frame_id=world` and `child_frame_id=base_link`
- The position follows a circle: `x = radius * cos(angle)`, `y = radius * sin(angle)`
- The orientation (yaw) always points in the direction of motion
- `robot_state_publisher` keeps publishing the TFs between links (body, head, legs...)
- RViz, with Fixed Frame = `world`, sees the entire TF tree and shows R2D2 moving

The result is a walking illusion: no real physics (no friction, gravity,
contacts), but visually convincing and perfect for learning how TF works.

---

## Package structure

```
r2d2_dancer/
├── README.md                          ← This file
├── LICENSE                            ← MIT License
├── setup.py                           ← Entry point and installation
├── package.xml                        ← ROS2 dependencies
├── .gitignore
├── r2d2_dancer/
│   ├── __init__.py
│   ├── state_publisher.py             ← The "choreographer" node (dancing on the spot)
│   └── base_mover.py                  ← The "walker" node (moves base_link)
├── urdf/
│   └── r2d2.urdf                      ← 3D model of the robot
├── launch/
│   ├── r2d2_dancer.launch.py          ← Launch: dancing on the spot
│   └── r2d2_walker.launch.py          ← Launch: dancing + walking in circles
├── rviz/
│   ├── r2d2.rviz                      ← RViz config (Fixed Frame: base_link)
│   └── r2d2_walker.rviz               ← RViz config (Fixed Frame: world)
├── video/
│   ├── README.md                      ← Instructions for recording videos
│   ├── r2d2_dancer.gif                ← Demo: dancing on the spot
│   └── r2d2_walker.gif                ← Demo: walking in circles
└── resource/
    └── r2d2_dancer
```

---

## Experimenting

The beauty of this example is that you can easily modify it:

### Change the dance speed
In `r2d2_dancer/state_publisher.py`, change the angle increment:

```python
self.angle += 0.1   # original: 20 Hz, 2 rad/s
self.angle += 0.2   # double speed
self.angle += 0.05  # half speed
```

### Add new parts to the robot
1. **URDF**: add a new `<link>` and a `<joint>`
2. **state_publisher.py**: add the joint name to the `joint_state.name` array and compute its position

### Change the colors
In the `urdf/r2d2.urdf` file, modify the RGBA values in `<material>`:
```xml
<material name="r2d2_blue">
    <color rgba="0.1 0.3 0.8 1.0"/>   <!-- R  G  B  Alpha (0.0–1.0) -->
</material>
```

### Add a different movement pattern
Try alternative functions in `timer_callback()`:
```python
# Jerky movement (sawtooth)
pos = (self.angle % 1.0) * 1.2 - 0.6

# Smooth random movement
import random
pos += (random.random() - 0.5) * 0.1
pos = max(-0.6, min(0.6, pos))
```

### Modify the walking path
In `r2d2_dancer/base_mover.py`, change the movement pattern:
```python
# Larger circle
self.radius = 3.0

# Straight line (remove sin/cos)
t.transform.translation.x = self.angle * 0.5  # move forward along X
t.transform.translation.y = 0.0

# Spiral (radius grows over time)
r = 0.5 + self.angle * 0.1
t.transform.translation.x = r * cos(self.angle)
t.transform.translation.y = r * sin(self.angle)
```

---

## Troubleshooting

| Problem | Solution |
|----------|-----------|
| RViz shows nothing | Open the launch with the config (`-d rviz/r2d2.rviz`). Alternatively, manually add "RobotModel" and set Fixed Frame to `base_link`. |
| The robot is frozen | Verify that `state_publisher` is running: `ros2 node list`. If missing, check the logs. |
| Parts are disconnected | The joint names in `state_publisher.py` must **exactly match** those in the URDF (case-sensitive!). |
| RViz crashes / lags | If you have an integrated GPU, try lowering the timer rate in `state_publisher.py` (e.g. `0.1` instead of `0.05`). |
| `colcon build` fails | Make sure all dependencies are installed: `sudo apt install ros-humble-robot-state-publisher ros-humble-rviz2` |

---

## License

MIT — see the [LICENSE](LICENSE) file for details.

---

*Created as an educational example for learning ROS2, URDF, JointState, and TF. Perfect for students and beginners.*
