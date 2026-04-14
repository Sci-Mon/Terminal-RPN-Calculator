@echo off
py rpn.py

if %ERRORLEVEL% EQU 0 (
    exit
) else (
    echo An error has occurred (Code: %ERRORLEVEL%).
    pause
)