# CSM Python API Library

## Installation

```
# from PyPI
pip install csm-ai

# from source
pip install git+https://github.com/CommonSenseMachines/csm-ai.git
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

mesh_path = csm_client.image_to_3d(image_path, mesh_format='glb')

# b) using an image URL
image_url = "https://upload.wikimedia.org/wikipedia/en/a/a9/MarioNSMBUDeluxe.png"

mesh_path = csm_client.image_to_3d(image_url, mesh_format='obj')
```
To make the output 3D asset aligned with the user-specified dimensions, you may add one more parameter in the image_to_3d function call
```
mesh_path = csm_client.image_to_3d(image_path, mesh_format='glb', scaled_bbox=(0.8,0.8,05))
``` 
where scaled_bbox specify the width, height and depth, respectively.


Run a `text-to-3d` job:

```python
prompt = "3d asset of a character head, cartoon style, low poly, front view"

mesh_path, image_path = csm_client.text_to_3d(prompt, mesh_format='glb')
```

**Mesh formats:** Choose any of ['obj', 'glb', 'usdz'] for the `mesh_format` argument.

**Verbose mode:** Run client functions with option `verbose=True` (the default) to see additional status messages and logs.

