# TURTLE Robotics SI — ROS 2 Environment Setup (PowerShell)
# Run this in PowerShell before using docker compose on Windows.
# Usage: . .\ROS2-Environment.ps1

$env:COMPOSE_PROJECT_NAME = "turtle-si"
$env:ROS_DOMAIN_ID = "0"
$env:GZ_PARTITION = "turtle_si"

Write-Host "TURTLE SI environment set." -ForegroundColor Green
Write-Host "  COMPOSE_PROJECT_NAME = $env:COMPOSE_PROJECT_NAME"
Write-Host "  ROS_DOMAIN_ID        = $env:ROS_DOMAIN_ID"
Write-Host "  GZ_PARTITION         = $env:GZ_PARTITION"
