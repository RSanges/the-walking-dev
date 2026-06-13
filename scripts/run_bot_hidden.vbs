' Launch the Telegram bot with the venv's python.exe, hidden (no console).
' Used by the TheWalkingDev-Bot scheduled task. Portable: derives the repo root
' from this script's location (scripts\ -> repo root). We use python.exe (not
' pythonw.exe) because uv-managed CPython ships without pythonw.exe.
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = root
' Window style 0 = hidden, bWaitOnReturn = True so wscript stays alive for the
' bot's lifetime. This keeps the scheduled-task job object alive (otherwise the
' Task Scheduler kills the python child as soon as wscript exits).
sh.Run """" & root & "\.venv\Scripts\python.exe"" -m walkingdev.cli bot", 0, True
