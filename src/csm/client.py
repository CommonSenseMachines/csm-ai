import os
import time
from urllib.request import urlretrieve
import requests


class BackendClient:
    def __init__(
            self,
            api_key=None,
            base_url="https://api.csm.ai:5566",
        ):
        if api_key is None:
            api_key = os.environ.get('CSM_API_KEY')
            if api_key is None:
                raise Exception(
                    "The argument `api_key` must be provided when env variable "
                    "CSM_API_KEY is not set."
                )
        self.api_key = api_key
        self.base_url = base_url

    @property
    def headers(self):
        return {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }

    # image-to-3d API
    # -------------------------------------------

    def create_image_to_3d_session(
            self,
            image_url,
            *,
            preview_mesh="turbo",
            #manual_segmentation=False,
            auto_gen_3d=False,
            ## preview args (turbo)
            diffusion_time_steps=75,
            ## refine args
            pixel_alignment="highest",
            model_resolution="high",
            polygon_count="high_poly",
            topology="tris",
            texture_resolution=2048,
        ):
        """Initialize an image-to-3d session.
        """
        assert preview_mesh in ["turbo", "hd"]
        assert 16 <= diffusion_time_steps <= 200
        assert pixel_alignment in ["lowest", "highest"]
        assert model_resolution in ["low", "high"]
        assert polygon_count in ["low_poly", "high_poly"]
        assert topology in ["tris", "quads"]
        assert 128 <= texture_resolution <= 2048

        parameters = {
            "image_url": image_url,
            "preview_mesh": preview_mesh,
            "pixel_alignment": pixel_alignment,
            "model_resolution": model_resolution,
            "resolution": polygon_count,
            "diffusion_time_steps": diffusion_time_steps,
            "auto_gen_3d": auto_gen_3d,
            "topology": topology,
            "texture_resolution": texture_resolution,
        }

        response = requests.post(
            url=os.path.join(self.base_url, "image-to-3d-sessions"),
            json=parameters,
            headers=self.headers,
        )

        return response.json()

    def get_image_to_3d_session_info(self, session_code):
        response = requests.get(
            url=os.path.join(self.base_url, "image-to-3d-sessions", session_code),
            headers=self.headers,
        )

        return response.json()
    
    def get_3d_refine(self, session_code):
        response = requests.post(
            url=os.path.join(self.base_url, "image-to-3d-sessions", "get-3d", "refine", session_code),
            headers=self.headers,
        )

        return response.json()
    
    def get_3d_preview(self, session_code, selected_spin_index=0, selected_spin_url=None):
        if selected_spin_url:
            data = self.get_image_to_3d_session_info(session_code)['data']
            spins = data['spins']
            selected_spin_url = spins[selected_spin_index]["image_url"]

        parameters = {
            "selected_spin_index": selected_spin_index,
            "selected_spin": selected_spin_url,
        }

        response = requests.post(
            url=os.path.join(self.base_url, "image-to-3d-sessions", "get-3d", "preview", session_code),
            json=parameters,
            headers=self.headers,
            timeout=100,
        )

        return response.json()

    # text-to-image API methods
    # -------------------------------------------

    def create_text_to_image_session(
            self,
            prompt,
            style_id="",
            guidance=6,
        ):
        """Initialize a text-to-image session.
        """
        parameters = {
            'prompt': str(prompt),
            'style_id': str(style_id),
            'guidance': str(guidance),
        }

        response = requests.post(
            url=os.path.join(self.base_url, "tti-sessions"),
            json=parameters,
            headers=self.headers,
        )

        return response.json()

    def get_text_to_image_session_info(self, session_code):
        response = requests.get(
            url=os.path.join(self.base_url, "tti-sessions", session_code),
            headers=self.headers,
        )

        return response.json()


class CSMClient:
    def __init__(
            self,
            api_key=None,
            base_url="https://api.csm.ai:5566",
        ):
        self.backend = BackendClient(api_key=api_key, base_url=base_url)

    def image_to_3d(
            self,
            image_url,
            diffusion_time_steps=75,
            mesh_format='obj',
            output='./',
            timeout=200,
            verbose=False,
        ):
        mesh_format = mesh_format.lower()
        assert mesh_format in ['obj', 'glb', 'usdz']

        os.makedirs(output, exist_ok=True)

        # initialize session
        result = self.backend.create_image_to_3d_session(
            image_url,
            preview_mesh="turbo",
            diffusion_time_steps=diffusion_time_steps,
            auto_gen_3d=False,
        )
        session_code = result['data']['session_code']

        if verbose:
            print(f'[INFO] Image-to-3d session created ({session_code})')
            print(f'[INFO] Running preview spin generation...')

        # wait for preview spin generation to complete (20-30s)
        start_time = time.time()
        while True:
            time.sleep(2)
            result = self.backend.get_image_to_3d_session_info(session_code)
            if result['data']['status'] == 'spin_generate_done':
                break
            run_time = time.time() - start_time
            if run_time >= timeout:
                raise RuntimeError("Preview spin generation timed out")
        
        if verbose:
            print(f'[INFO] Preview spin generation completed in {run_time:.1f}s')
            print(f'[INFO] Running preview mesh export...')

        # TODO: API option for a single generation (vs. batch of 4)
        selected_spin_index = 1
        selected_spin_url = result['data']['spins'][selected_spin_index]["image_url"]

        # download spin video
        spin_path = os.path.join(output, 'spin.mp4')
        urlretrieve(selected_spin_url, spin_path)

        # launch preview mesh export
        result = self.backend.get_3d_preview(
            session_code,
            selected_spin_index=selected_spin_index,
            selected_spin_url=selected_spin_url,
        )

        # wait for preview mesh export to complete (20-30s)
        start_time = time.time()
        while True:
            time.sleep(2)
            result = self.backend.get_image_to_3d_session_info(session_code)
            if result['data']['status'] == 'preview_done':
                break
            run_time = time.time() - start_time
            if run_time >= timeout:
                raise RuntimeError("Preview mesh export timed out")
            
        if verbose:
            print(f'[INFO] Preview mesh export completed in {run_time:.1f}s')

        # download mesh file based on the requested format
        if mesh_format == 'obj':
            mesh_url = result['data']['preview_mesh_url_zip']
            mesh_file = 'mesh.zip'
        elif mesh_format == 'glb':
            mesh_url = result['data']['preview_mesh_url_glb']
            mesh_file = 'mesh.glb'
        elif mesh_format == 'usdz':
            mesh_url = result['data']['preview_mesh_url_usdz']
            mesh_file = 'mesh.usdz'
        else:
            raise ValueError(f"Encountered unexpected mesh_format value ('{mesh_format}').")

        mesh_path = os.path.join(output, mesh_file)  # TODO: os.path.abspath ?

        urlretrieve(mesh_url, mesh_path)

        return spin_path, mesh_path

    def text_to_3d(
            self,
            prompt,
            style_id="",
            guidance=6,
            diffusion_time_steps=75,
            mesh_format='obj',
            output='./',
            timeout=200,
            verbose=False,
        ):
        os.makedirs(output, exist_ok=True)

        # initialize text-to-image session
        result = self.backend.create_text_to_image_session(
            prompt,
            style_id=style_id,
            guidance=guidance,
        )
        session_code = result['data']['session_code']

        if verbose:
            print(f'[INFO] Text-to-image session created ({session_code})')
            print(f'[INFO] Running text-to-image generation...')

        # wait for image generation to complete
        start_time = time.time()
        while True:
            time.sleep(2)
            result = self.backend.get_text_to_image_session_info(session_code)
            if result['data']['status'] == 'completed':
                break
            # assert result['data']['status'] == 'processing'  # TODO
            run_time = time.time() - start_time
            if run_time >= timeout:
                raise RuntimeError("Text-to-image generation timed out")

        if verbose:
            print(f'[INFO] Text-to-image generation completed in {run_time:.1f}s')

        # access the image URL
        image_url = result['data']['image_url']

        # download image
        image_path = os.path.join(output, 'image.png')
        urlretrieve(image_url, image_path)

        # launch image-to-3d
        spin_path, mesh_path = self.image_to_3d(
            image_url,
            diffusion_time_steps=diffusion_time_steps,
            mesh_format=mesh_format,
            output=output,
            timeout=timeout,
            verbose=verbose
        )

        return image_path, spin_path, mesh_path
