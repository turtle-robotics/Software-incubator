from setuptools import find_packages, setup

package_name = "turtle_control"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/turtle_control"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TURTLE Robotics",
    maintainer_email="turtle@tamu.edu",
    description="TURTLE Robotics SI control nodes for turtle_bot.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "drive_turtle = turtle_control.drive_turtle:main",
            "arm_control  = turtle_control.arm_control:main",
        ],
    },
)
