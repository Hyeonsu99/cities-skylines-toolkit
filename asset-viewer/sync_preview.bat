@echo off
rem Copy the latest builds of every cs2-kit project into public\preview for the viewer.
rem Usage: sync_preview.bat [project pattern]   e.g. sync_preview.bat exllu-*   (default: all projects)
setlocal
set "PAT=%~1"
if "%PAT%"=="" set "PAT=*"
set "DST=%~dp0public\preview"
if not exist "%DST%" mkdir "%DST%"
set N=0
for /d %%P in ("%~dp0..\cs2-kit\projects\%PAT%") do (
 for /d %%A in ("%%P\output\*") do (
  if exist "%%A\%%~nxA.fbx" (
   for %%S in (.fbx _Win.fbx _Gls.fbx _BaseColor.png _Normal.png _MaskMap.png _Emissive.png) do if exist "%%A\%%~nxA%%S" copy /y "%%A\%%~nxA%%S" "%DST%\" >nul
   echo   %%~nxA
   set /a N+=1
  )
 )
)
echo %N% assets copied to public\preview
