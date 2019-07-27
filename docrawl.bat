@echo off

@rem //Get administrator privileges
set "params=%*"
cd /d "%~dp0" && ( if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs" ) && fsutil dirty query %systemdrive% 1>nul 2>nul || (  echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && exit /B )

@rem //Run python from relative path, feel free to use --size here to create a size-specific preset.
@rem //Example: python %~dp0crawler.py --size 4096 
python %~dp0crawler.py

@rem //Close window in 60sec
timeout 60
exit 0