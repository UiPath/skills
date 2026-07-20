@echo off
REM Windows wrapper so bare `uip` resolves on cmd / PowerShell PATH lookup.
REM Delegates to the python mock script next to this file.
python "%~dp0uip" %*
