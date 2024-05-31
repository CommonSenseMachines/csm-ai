from csm import CSMClient

csm_client = CSMClient(api_key='xxx')

#using a local image path or image_url
image_url = "/path/to/your/sofa.png"
#specify the width, height, and depth of the target object
scaled_bbox = [0.86, 0.86, 0.1]    
#generate preview mesh and download it.
mesh_path = csm_client.image_to_3d(image_url, mesh_format='obj', generate_spin_video = False, scaled_bbox=scaled_bbox)

print(f"Mesh path: {mesh_path}")