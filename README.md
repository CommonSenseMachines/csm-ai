# CSM Python API Library

## Installation
TODO: the first installation option (PyPI) does not yet work. Coming soon.
```
# from PyPI
pip install csm

# from source
pip install git+https://github.com/CommonSenseMachines/csm-python.git
```

## Usage

Initialize the API client:

```python
from csm import CSMClient

csm_client = CSMClient(api_key='6bCfF4467bXXXXXX4E6B271BeC5')
```

Run an `image-to-3d` job:

```python
image_url = "https://upload.wikimedia.org/wikipedia/en/a/a9/MarioNSMBUDeluxe.png"

spin_path, mesh_path = csm_client.image_to_3d(image_url, mesh_format='glb')
```

Run a `text-to-3d` job:

```python
prompt = "3d asset of a character head, cartoon style, low poly, front view"

image_path, spin_path, mesh_path = csm_client.text_to_3d(prompt, mesh_format='glb')
```
