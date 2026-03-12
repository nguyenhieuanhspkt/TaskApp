@echo off
REM --- Hi?n th? thông báo tru?c khi ch?y app ---
echo ? Ðang loading app... ch? xíu

REM --- Thi?t l?p các bi?n môi tru?ng tr?c ti?p ---
set FIREBASE_SERVICE_ACCOUNT_PATH=Firebase/FirebaseCred.json
set FIREBASE_DATABASE_URL=https://taskapp-7d0e5-default-rtdb.asia-southeast1.firebasedatabase.app/

set MYEMAIL=hieuna@vinhtan4tpp.evn.vn
set MYPASSEMAIL=Abcd@123456
set EWS_URL=https://mail.vinhtan4tpp.evn.vn/EWS/Exchange.asmx

REM --- Ch?y file EXE c?a b?n ---
start main.exe

pause
