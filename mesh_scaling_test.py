from csm import CSMClient

csm_client = CSMClient(api_key='C6544b919C9DD82cccdF41d5D4778043')

# a) using a local image path
image_path = "/media/shuda/ssd2t/front_back/sheets/x512/6/0_rgba.png"

mesh_path = csm_client.image_to_3d(image_path, mesh_format='obj', generate_spin_video = True, scaled_bbox=(0.8,0.8,0.1))

print(f"Mesh path: {mesh_path}")