from csm import CSMClient

# NOTE: replace with a valid API key
breakpoint()
csm_client = CSMClient(api_key='C6544b919C9DD82cccdF41d5D4778043')

# a) using a local image path
image_url = "https://imageto3d.blob.core.windows.net/data/test/guard/0_rgba.png?sp=r&st=2024-05-23T14:35:54Z&se=2025-05-23T22:35:54Z&spr=https&sv=2022-11-02&sr=b&sig=TOPUyeztCcwyqqy60CB3ghREYG8N3UevpU3CQesWk0w%3D"

mesh_path = csm_client.image_to_3d(image_url, mesh_format='glb')

print(f"Mesh path: {mesh_path}")