python -m venv .venv-cloan

.venv-cloan/Scripts/activate

pip install -r requirements.txt

((Get-Content -path ".4-venv-cloan\Lib\site-packages\utoken\util.py" -Raw).Replace("with open(filename)", "with open(filename, encoding='utf-8')") | Set-Content -Path ".4-venv-cloan\Lib\site-packages\utoken\util.py")
echo -e ".venv-cloan\nsetup.bat" > .gitignore
mkdir "data\marking"
mkdir "data\output"
rm setup.sh

git pull