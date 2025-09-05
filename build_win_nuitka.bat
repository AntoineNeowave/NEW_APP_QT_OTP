@echo off
echo Build enterprise avec techniques anti-faux-positifs...

rem Nettoyage complet
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.dist rmdir /s /q *.dist

rem Build avec Nuitka - options enterprise
python -m nuitka ^
  --onefile --onefile-no-compression ^
  --enable-plugin=pyqt6 ^
  --include-data-dir=ui=ui ^
  --include-data-dir=images=images ^
  --include-data-dir=locales=locales ^
  --windows-icon-from-ico=images/logo.ico ^
  --output-dir=dist ^
  --output-filename=NeoOTP.exe ^
  --remove-output ^
  --windows-console-mode=disable ^
  --windows-product-name="NEOWAVE OTP Manager" ^
  --windows-company-name="NEOWAVE" ^
  --windows-product-version="1.0.0.0" ^
  --windows-file-version="1.0.0.0" ^
  --windows-file-description="NEOWAVE OTP Manager" ^
  --show-progress ^
  main.py

echo.
echo Build terminé !
echo L'ajout de métadonnées Windows réduit les faux positifs
echo.
pause