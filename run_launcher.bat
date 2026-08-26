@echo off
title 30-Day Project Suite Launcher
color 0B
cd /d "%~dp0"

:menu
cls
echo ================================================================
echo           30-DAY USEFUL & COOL APP SUITE LAUNCHER
echo ================================================================
echo.
echo  [1] Day 1: Infinite Wallpaper & Focus Studio (1-Click Wallpaper)
echo  [2] Day 2: Fractal Tree Studio & 4-7-8 Breathing Guide
echo  [3] Day 3: Swarm Ecosystem & Genetic Simulation (Draw Walls)
echo  [4] Day 4: Ergonomics, Blink Rate & Privacy Avatar
echo  [5] Day 5: AirDraw Pro (Whiteboard & Shape Auto-Beautifier)
echo  [6] Day 6: Neon Snake & Touchless PC Remote Controller
echo  [7] Day 7: Digital Soul Multimodal AI & Daily Notes Assistant
echo  [8] Day 7_2: Virtual Piano & Music Studio (Chords & Metronome)
echo  [9] Day 7_3: Typing Analyzer Pro (Developer Code & Study Notes)
echo  [10] Lumina Language: Run Budget Calculator
echo  [11] Lumina Language: Run Unit Converter
echo  [12] Lumina Language: Run Daily Task Logger
echo  [13] Lumina Language: Run Statistics Engine
echo  [0] Exit
echo.
echo ================================================================
set /p choice="Select an application to launch [0-13]: "

if "%choice%"=="1" (
    start "" .venv\Scripts\python.exe Day_1\infinte_wallpapers.py
    goto menu
)
if "%choice%"=="2" (
    start "" .venv\Scripts\python.exe Day_2\faractor_tree_generator.py
    goto menu
)
if "%choice%"=="3" (
    start "" .venv\Scripts\python.exe Day_3\Artificial_Life_Simulation.py
    goto menu
)
if "%choice%"=="4" (
    start "" .venv\Scripts\python.exe Day_4\main.py
    goto menu
)
if "%choice%"=="5" (
    start "" .venv\Scripts\python.exe Day_5\airdraw_pro.py
    goto menu
)
if "%choice%"=="6" (
    start "" .venv\Scripts\python.exe Day_6\main.py
    goto menu
)
if "%choice%"=="7" (
    start "" .venv\Scripts\python.exe Day_7\main.py
    goto menu
)
if "%choice%"=="8" (
    start "" .venv\Scripts\python.exe Day_7_2\piano.py
    goto menu
)
if "%choice%"=="9" (
    start "" .venv\Scripts\python.exe Day_7_3\main.py
    goto menu
)
if "%choice%"=="10" (
    .venv\Scripts\python.exe main.py samples\budget_calculator.lum
    pause
    goto menu
)
if "%choice%"=="11" (
    .venv\Scripts\python.exe main.py samples\unit_converter.lum
    pause
    goto menu
)
if "%choice%"=="12" (
    .venv\Scripts\python.exe main.py samples\todo_tracker.lum
    pause
    goto menu
)
if "%choice%"=="13" (
    .venv\Scripts\python.exe main.py samples\math_statistics.lum
    pause
    goto menu
)
if "%choice%"=="0" exit
goto menu
