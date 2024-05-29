from csm import CSMClient

csm_client = CSMClient(api_key='C6544b919C9DD82cccdF41d5D4778043')

#using a local image path or image_url
image_url = "https://imageto3d.blob.core.windows.net/data/test/guard/0_rgba.png?sp=r&st=2024-05-23T14:35:54Z&se=2025-05-23T22:35:54Z&spr=https&sv=2022-11-02&sr=b&sig=TOPUyeztCcwyqqy60CB3ghREYG8N3UevpU3CQesWk0w%3D"
#specify the width, height, and depth of the target object
scaled_bbox = [0.86, 0.86, 0.1]    
#generate preview mesh and download it.
mesh_path = csm_client.image_to_3d(image_url, mesh_format='obj', generate_spin_video = True, scaled_bbox=scaled_bbox)

print(f"Mesh path: {mesh_path}")