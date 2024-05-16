# CSM Python API Library

## Installation

```
# from PyPI (coming soon)
pip install csm

# from source
pip install git+https://github.com/CommonSenseMachines/csm-python.git
```

## Usage

Initialize the API client:

```python
from csm import CSMClient

# NOTE: replace with a valid API key
csm_client = CSMClient(api_key='6bCfF4467bXXXXXX4E6B271BeC5')
```

Run an `image-to-3d` job:

```python
# a) using a local image path
image_path = "/path/to/image.png"

spin_path, mesh_path = csm_client.image_to_3d(image_path, mesh_format='glb', verbose=True)

# b) using an image URL
image_url = "https://upload.wikimedia.org/wikipedia/en/a/a9/MarioNSMBUDeluxe.png"

spin_path, mesh_path = csm_client.image_to_3d(image_url, mesh_format='obj')
```

Run a `text-to-3d` job:

```python
prompt = "3d asset of a character head, cartoon style, low poly, front view"

image_path, spin_path, mesh_path = csm_client.text_to_3d(prompt, mesh_format='glb')
```

**Mesh formats:** Choose any of ['obj', 'glb', 'usdz'] for the `mesh_format` argument.

**Verbose mode:** Run client functions with option `verbose=True` to see additional status messages and logs.

