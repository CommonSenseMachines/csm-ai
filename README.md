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

Quick start basic usage example:

```python
from csm import CSMClient

csm_client = CSMClient(api_key='6bCfF4467bXXXXXX4E6B271BeC5')

image_url = "https://upload.wikimedia.org/wikipedia/en/a/a9/MarioNSMBUDeluxe.png"

spin_mp4, mesh_obj_zip, mesh_glb, mesh_usdz = csm_client.image_to_3d(image_url)
```
