import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'r2d2_dancer'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Includi i file URDF
        ('share/' + package_name + '/urdf',
            glob('urdf/*.urdf')),
        # Includi i file launch
        ('share/' + package_name + '/launch',
            glob('launch/*.launch.py')),
        # Includi i file di configurazione RViz
        ('share/' + package_name + '/rviz',
            glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='matteo',
    maintainer_email='m.pedone2000@gmail.com',
    description='R2D2 danzante - esempio didattico ROS2 con URDF e RViz',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'state_publisher = r2d2_dancer.state_publisher:main',
            'base_mover = r2d2_dancer.base_mover:main',
        ],
    },
)
