Quick Start
============

Initialize the API client:

.. code-block:: python

    from csm import CSMClient

    # NOTE: replace with a valid API key
    csm_client = CSMClient(api_key='6bCfF4467bXXXXXX4E6B271BeC5')


Run image-to-3d inference:

.. code-block:: python

    # input a local image path (also supported: url, PIL.Image.Image)
    image_path = "/path/to/image.png"
    result = csm_client.image_to_3d(image_path, mesh_format='glb')

    print(result.mesh_path)


Run text-to-3d inference:

.. code-block:: python

    prompt = "3d asset of a character head, cartoon style, low poly, front view"
    result = csm_client.text_to_3d(prompt, mesh_format='obj')

    print(result.mesh_path)


**Mesh formats:** Choose any of ['obj', 'glb', 'fbx', 'usdz'] for the `mesh_format` argument.

**Verbose mode:** Run client functions with option `verbose=True` (the default) to see additional status messages and logs.
