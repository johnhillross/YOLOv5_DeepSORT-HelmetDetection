@echo off
for /d %%i in (D:\#Data\Detect\*) do (
    rd %%i /s/q
)
"%MYSQL_HOME%\bin\mysql" -h localhost -u root -p123456 -e "use eb_helmet; truncate table eb_rider;"
pause