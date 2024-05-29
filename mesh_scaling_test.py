from csm import CSMClient

csm_client = CSMClient(api_key='C6544b919C9DD82cccdF41d5D4778043')

#using a local image path
image_path = "/media/shuda/ssd2t/front_back/sheets/x512/29/0.jpg" 
#specify the width, height, and depth of the target object
scaled_bbox = [0.86, 0.86, 0.1]    
#generate preview mesh and download it.
mesh_path = csm_client.image_to_3d(image_path, mesh_format='obj', generate_spin_video = True, scaled_bbox=scaled_bbox)

print(f"Mesh path: {mesh_path}")