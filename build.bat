@echo off
echo ============================================
echo Building Mercari Wishlist to EXE
echo ============================================

REM Check if venv exists and activate it
if exist "venv-local\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv-local\Scripts\activate.bat
) else (
    echo Warning: venv-local not found, using system Python
)

REM Install PyInstaller if not installed
echo Installing/Updating PyInstaller...
pip install pyinstaller

REM Install playwright browsers (required for DynamicFetcher)
echo Installing Playwright browsers...
playwright install chromium

REM Build the exe
echo Building EXE...
pyinstaller --clean mercari_wishlist.spec

echo ============================================
echo Build complete!
echo EXE location: dist\MercariWishlist.exe
echo ============================================
echo.
echo IMPORTANT: Copy brand.json to the same folder as the EXE
echo if you want to modify brands after distribution.
echo ============================================
pause
