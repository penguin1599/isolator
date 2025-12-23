@echo off
REM Build and run the audio cleaner with GPU support
REM Automatically detects RTX 5090 and uses appropriate Dockerfile

REM Check GPU model using PowerShell (more reliable on Windows)
FOR /F "tokens=*" %%G IN ('powershell -Command "(nvidia-smi --query-gpu=name --format=csv,noheader 2>$null) -replace '\s+$','' "') DO SET GPU_NAME=%%G

REM Select Dockerfile based on GPU
echo [*] Detected GPU: %GPU_NAME%
echo %GPU_NAME% | findstr /I "5090 5080 5070" >nul
if %ERRORLEVEL% EQU 0 (
    echo [*] Using Blackwell-optimized Dockerfile ^(CUDA 12.8 + PyTorch nightly^)
    SET DOCKERFILE=Dockerfile.5090
    SET IMAGE_TAG=audio-cleaner:5090
) else (
    echo [*] Using standard Dockerfile ^(CUDA 12.1 + PyTorch stable^)
    SET DOCKERFILE=Dockerfile
    SET IMAGE_TAG=audio-cleaner:latest
)

REM Build the image
docker build -t %IMAGE_TAG% -f %DOCKERFILE% .

REM Run with GPU access, mount input/output directories
REM If no argument given, process all files in input/
if "%1"=="" (
    echo [*] Processing all files in input/ directory...
    docker run --rm -it ^
        --gpus all ^
        -v "%cd%\input:/input" ^
        -v "%cd%\output:/output" ^
        %IMAGE_TAG% "/input" -o "/output"
) else (
    REM Process specific file from input folder
    docker run --rm -it ^
        --gpus all ^
        -v "%cd%\input:/input" ^
        -v "%cd%\output:/output" ^
        %IMAGE_TAG% "/input/%1" -o "/output"
)
