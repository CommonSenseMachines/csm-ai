from csm import CSMClient

csm_client = CSMClient(api_key='C6544b919C9DD82cccdF41d5D4778043')

#using a local image path or image_url
# image_url = "https://imageto3d.blob.core.windows.net/data/test/guard/0_rgba.png?sp=r&st=2024-05-23T14:35:54Z&se=2025-05-23T22:35:54Z&spr=https&sv=2022-11-02&sr=b&sig=TOPUyeztCcwyqqy60CB3ghREYG8N3UevpU3CQesWk0w%3D"
image_url = "/home/shuda/Downloads/tmp/sofa.png"
#specify the width, height, and depth of the target object
scaled_bbox = [0.86, 0.86, 0.86]    
#generate preview mesh and download it.
mesh_path = csm_client.image_to_3d(image_url, mesh_format='obj', generate_spin_video = True, scaled_bbox=scaled_bbox)

print(f"Mesh path: {mesh_path}")

import json
import requests
import time

headers = { 'Content-Type': 'application/json', 'x-api-key': 'C6544b919C9DD82cccdF41d5D4778043'}
print('generating refine mesh...')    
url = f"https://devapi.csm.ai/image-to-3d-sessions/get-3d/refine/{csm_client.session_code}"
payload = json.dumps({"scaled_bbox": scaled_bbox})
response = requests.request("POST", url, headers=headers, data=payload)
while True:
    time.sleep(60*5)
    response = requests.get(f"https://devapi.csm.ai/image-to-3d-sessions/{csm_client.session_code}", headers=headers)
    imageTo3dSession = response.json()['data']
    print(imageTo3dSession['status'] )
    if imageTo3dSession['status'] == 'refine_done':
        print('refine mesh done and you can down from:')
        print(imageTo3dSession['mesh_url_zip'])
        break