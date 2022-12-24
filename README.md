# Subsystems

Subsystems is a high-level interface for (web) applications
and it has the official interface for Rocketry.
Subsystems unifies several frameworks into one configuration 
under the same syntax making it easy to develop and deploy
web apps.

Supported application frameworks:

- FastAPI
- Flask
- Rocketry

Supported web server frameworks:

- Uvicorn
- Waitress
- Werkzeug
- Guvicorn (experimential)

## Installation

Pip install:

```console
pip install subsystems
```

## Examples

Create Subsystems configuration file:

```console
python -m subsystems init rocketry
```

Create a scheduler to ``scheduler.py``:

```python
from rocketry import Rocketry

app = Rocketry()

@app.task()
def do_things():
    ...
```

Start the system

```console
python -m subsystems launch --scheduler scheduler:app
```


Author: [Mikael Koli](https://github.com/Miksus)