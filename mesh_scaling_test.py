from csm import CSMClient

csm_client = CSMClient(api_key='xxx')

#using a local image path or image_url
image_url = "./assets/sofa.png"
#specify the width, height, and depth of the target object
scaled_bbox = [0.86, 0.86, 0.5]    
#generate preview mesh and download it.
mesh_path = csm_client.image_to_3d(image_url, mesh_format='obj', scaled_bbox=scaled_bbox)

print(f"Mesh path: {mesh_path}")

# enable the following code to refine the preview mesh
# import json
# import requests
# import time

# headers = { 'Content-Type': 'application/json', 'x-api-key': 'C6544b919C9DD82cccdF41d5D4778043'}
# print('generating refine mesh...')    
# url = f"https://devapi.csm.ai/image-to-3d-sessions/get-3d/refine/{csm_client.session_code}"
# payload = json.dumps({"scaled_bbox": scaled_bbox})
# response = requests.request("POST", url, headers=headers, data=payload)
# while True:
#     time.sleep(60*5)
#     response = requests.get(f"https://devapi.csm.ai/image-to-3d-sessions/{csm_client.session_code}", headers=headers)
#     imageTo3dSession = response.json()['data']
#     print(imageTo3dSession['status'] )
#     if imageTo3dSession['status'] == 'refine_done':
#         print('refine mesh done and you can down from:')
#         print(imageTo3dSession['mesh_url_zip'])
#         break