python -m venv .venv-cloan

.venv-cloan/Scripts/activate

pip install -r requirements.txt

echo -e ".venv-cloan\nsetup.bat" > .gitignore
mkdir "data\marking"
mkdir "data\output"
rm setup.sh

git pull