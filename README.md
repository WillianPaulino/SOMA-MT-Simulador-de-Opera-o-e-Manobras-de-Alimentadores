# Simulador/Unifilar – W0321P3

## Rodar local (Windows, Python 3.13 ok)
```bat
cd sim-w0321p3\backend
py -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
uvicorn app.main:app --reload
"# SOMA-MT-Simulador-de-Opera-o-e-Manobras-de-Alimentadores" 
