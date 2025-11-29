# Генеруємо requirements.txt (для встановлення всіх пакетів потрібний python 3.11)
pipreqs . --encoding=utf-8 --ignore .venv,__pycache__,build,dist
