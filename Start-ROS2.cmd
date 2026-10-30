@echo off
REM TURTLE Robotics SI — Build image and start the container
REM Double-click this file on Windows to get started.

echo Building TURTLE SI Docker image...
docker compose build

echo Starting container...
docker compose up -d

echo.
echo Done! Now run Run-ROS2.cmd to open a shell inside the container.
pause
