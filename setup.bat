@echo off
(
    @echo on
    python -m venv .venv-cloan
    call .\.venv-cloan\Scripts\activate.bat
    pip install -r requirements.txt
) &&(
    powershell -Command  "((Get-Content -path .venv-cloan\Lib\site-packages\utoken\util.py -Raw).Replace('with open(filename)', 'with open(filename, encoding=''utf-8'')') | Set-Content -Path .venv-cloan\Lib\site-packages\utoken\util.py)"
)
    echo .venv-cloan> .gitignore
    echo setup.bat>> .gitignore
    echo setup.sh>> .gitignore

    mkdir "data\marking"
    mkdir "data\output"

    del setup.sh

    git pull

    deactivate