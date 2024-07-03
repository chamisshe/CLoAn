python3 -m venv .venv-cloan

source .venv-cloan/bin/activate

python3 -m pip install -r requirements.txt

if [[ $OSTYPE -eq "linux-gnu" ]]
then
    echo "because of the PyAutoGui module, scrot, python3-tk and python3-dev need to also be installed."
    sudo apt-get install scrot
    sudo apt-get install python3-tk
    sudo apt-get install python3-dev
fi

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
