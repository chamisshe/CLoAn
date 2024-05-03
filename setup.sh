python3 -m venv .venv-cloan

source .venv-cloan/bin/activate

pip install -r requirements.txt

# modify the utoken package to fix a bug
sed -i "s/with open(filename)/with open(filename, encoding='utf-8')/g" .venv-cloan/lib64/*/site-packages/utoken/util.py
sed -i "s/with open(filename)/with open(filename, encoding='utf-8')/g" .venv-cloan/lib/*/site-packages/utoken/util.py

echo .venv-cloan > .gitignore
echo setup.bat >> .gitignore
echo setup.sh >> .gitignore
echo activate.sh >> .gitignore

mkdir "data/marking"
mkdir "data/output"

rm setup.bat

git pull
