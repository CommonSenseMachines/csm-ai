from csm import CSMClient

csm_client = CSMClient(api_key='xxx')

#using a local image path or image_url
image_url = "./assets/sofa.png"
#specify the width, height, and depth of the target object
scaled_bbox = [0.86, 0.86, 0.5]    
#generate preview mesh and download it.
mesh_path = csm_client.image_to_3d(image_url, mesh_format='obj', scaled_bbox=scaled_bbox)

print(f"Mesh path: {mesh_path}")