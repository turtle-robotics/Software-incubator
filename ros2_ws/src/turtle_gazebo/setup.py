from setuptools import find_packages, setup
import os
from glob import glob

package_name = "turtle_gazebo"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/turtle_gazebo"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.py")),
        (f"share/{package_name}/worlds", glob("worlds/*.sdf")),
        (f"share/{package_name}/models/turtle_bot",
            glob("models/turtle_bot/*")),
        (f"share/{package_name}/models/so101_arm",
            glob("models/so101_arm/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TURTLE Robotics",
    maintainer_email="turtle@tamu.edu",
    description="TURTLE Robotics SI Gazebo simulation package.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [],
    },
)
