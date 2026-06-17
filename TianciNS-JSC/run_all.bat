@echo off
cd /d "%~dp0"

echo ============================================
echo  TianciNS-JSC: Operator-Based NS Solver
echo  Extrapolation Tower (v2.6)
echo ============================================
echo.

echo Compiling tower_v26.exe ...
del tower_v26.exe 2>nul
g++ -O3 -std=c++17 -Wl,--stack,134217728 -o tower_v26.exe src\Tianci_NSDT_Tower_v2.6_JSC.cpp
if errorlevel 1 (
    echo.
    echo Compile FAILED.
    pause
    exit /b 1
)
echo Compile OK.
echo.

echo [1/3] Re=100 ...
tower_v26.exe --Re 100
echo.

echo [2/3] Re=400 ...
tower_v26.exe --Re 400
echo.

echo [3/3] Re=1000 ...
tower_v26.exe --Re 1000
echo.

echo Done. Results in results\Re100\  results\Re400\  results\Re1000
pause
