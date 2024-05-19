import os
import time
from urllib.request import urlretrieve
import requests
import base64
from io import BytesIO
from PIL import Image


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
            generate_preview_mesh=False,
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
            #"generate_preview_mesh": generate_preview_mesh,
            "pixel_alignment": pixel_alignment,
            "model_resolution": model_resolution,
            "resolution": polygon_count,
            "diffusion_time_steps": diffusion_time_steps,
            "auto_gen_3d": auto_gen_3d,
            "topology": topology,
            "texture_resolution": texture_resolution,
        }
        if generate_preview_mesh:
            parameters["generate_preview_mesh"] = True

        response = requests.post(
            url=f"{self.base_url}/image-to-3d-sessions",
            json=parameters,
            headers=self.headers,
        )

        return response.json()

    def get_image_to_3d_session_info(self, session_code):
        response = requests.get(
            url=f"{self.base_url}/image-to-3d-sessions/{session_code}",
            headers=self.headers,
        )

        return response.json()
    
    def get_3d_refine(self, session_code):
        response = requests.post(
            url=f"{self.base_url}/image-to-3d-sessions/get-3d/refine/{session_code}",
            headers=self.headers,
        )

        return response.json()
    
    def get_3d_preview(self, session_code, spin_url=None):
        selected_spin_index = 0

        if spin_url is None:
            result = self.get_image_to_3d_session_info(session_code)
            spin_url = result['data']['spins'][selected_spin_index]["image_url"]

        parameters = {
            "selected_spin_index": selected_spin_index,
            "selected_spin": spin_url,
        }

        response = requests.post(
            url=f"{self.base_url}/image-to-3d-sessions/get-3d/preview/{session_code}",
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
            url=f"{self.base_url}/tti-sessions",
            json=parameters,
            headers=self.headers,
        )

        return response.json()

    def get_text_to_image_session_info(self, session_code):
        response = requests.get(
            url=f"{self.base_url}/tti-sessions/{session_code}",
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

    def _handle_image_input(self, image):
        if isinstance(image, str):
            if os.path.isfile(image):  # local file path
                image_path = image
                pil_image = Image.open(image_path)
            else:  # URL for a web file
                image_url = image
                return image_url  # TODO: verify that this is a valid URL
        elif isinstance(image, Image.Image):
            pil_image = image
        else:
            raise ValueError(f"Encountered unexpected type for the input image.")
        
        return pil_image_to_x64(pil_image)

    def image_to_3d(
            self,
            image,
            generate_spin_video=False,  # TODO: deprecate this option
            diffusion_time_steps=75,
            mesh_format='obj',
            output='./',
            timeout=200,
            verbose=False,
        ):
        mesh_format = mesh_format.lower()
        if mesh_format not in ['obj', 'glb', 'usdz']:
            raise ValueError(
                f"Unexpected mesh_format value ('{mesh_format}'). Please choose "
                f"from options ['obj', 'glb', 'usdz']."
            )

        image_url = self._handle_image_input(image)

        os.makedirs(output, exist_ok=True)

        # initialize session
        result = self.backend.create_image_to_3d_session(
            image_url,
            preview_mesh="turbo",
            generate_preview_mesh=not generate_spin_video,
            diffusion_time_steps=diffusion_time_steps,
            auto_gen_3d=False,
        )

        status = result['data']['status']
        if (generate_spin_video and status != "spin_generate_processing") or (not generate_spin_video and status != "training_preview"):
            raise RuntimeError(f"Image-to-3d session creation failed (status='{status}')")

        session_code = result['data']['session_code']

        if verbose:
            print(f'[INFO] Image-to-3d session created ({session_code})')
            step_label = "spin generation" if generate_spin_video else "mesh generation"
            print(f'[INFO] Running preview {step_label}...')

        if generate_spin_video:
            # wait for preview spin generation to complete (20-30s)
            start_time = time.time()
            run_time = 0.
            while True:
                time.sleep(2)
                result = self.backend.get_image_to_3d_session_info(session_code)
                status = result['data']['status']
                if status == 'spin_generate_done':
                    break
                elif status == 'spin_generate_failed':
                    raise RuntimeError("Preview spin generation failed")
                else:
                    assert status == 'spin_generate_processing', f"status='{status}'"
                run_time = time.time() - start_time
                if run_time >= timeout:
                    raise RuntimeError("Preview spin generation timed out")
            
            if verbose:
                print(f'[INFO] Preview spin generation completed in {run_time:.1f}s')
                print(f'[INFO] Running preview mesh export...')

            # TODO: API option to skip spin rendering and go straight to mesh
            spin_url = result['data']['spins'][0]["image_url"]

            # download spin video
            spin_path = os.path.join(output, 'spin.mp4')
            urlretrieve(spin_url, spin_path)

            # launch preview mesh export
            result = self.backend.get_3d_preview(
                session_code,
                spin_url=spin_url,
            )

        else:
            spin_path = None

        # wait for preview mesh export to complete (20-30s)
        start_time = time.time()
        run_time = 0.
        while True:
            time.sleep(2)
            result = self.backend.get_image_to_3d_session_info(session_code)
            status = result['data']['status']
            if status == 'preview_done':
                break
            elif status == 'preview_failed':
                raise RuntimeError("Preview mesh export failed.")
            elif status != 'training_preview':
                raise RuntimeError(f"Unexpected error during preview mesh export (status='{status}')")
            run_time = time.time() - start_time
            if run_time >= timeout:
                raise RuntimeError("Preview mesh export timed out")
            
        if verbose:
            step_label = "mesh export" if generate_spin_video else "mesh generation"
            print(f'[INFO] Preview {step_label} completed in {run_time:.1f}s')

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
            generate_spin_video=False,
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

        status = result['data']['status']
        if status != "processing":
            raise RuntimeError(f"Text-to-image session creation failed (status='{status}')")

        session_code = result['data']['session_code']

        if verbose:
            print(f'[INFO] Text-to-image session created ({session_code})')
            print(f'[INFO] Running text-to-image generation...')

        # wait for image generation to complete
        start_time = time.time()
        run_time = 0.
        while True:
            time.sleep(2)
            result = self.backend.get_text_to_image_session_info(session_code)
            status = result['data']['status']
            if status == 'completed':
                break
            elif status != 'processing':
                raise RuntimeError(f"Unexpected error during text-to-image generation (status='{status}')")
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
            generate_spin_video=generate_spin_video,
            diffusion_time_steps=diffusion_time_steps,
            mesh_format=mesh_format,
            output=output,
            timeout=timeout,
            verbose=verbose
        )

        return image_path, spin_path, mesh_path


def pil_image_to_x64(image: Image.Image) -> str:
    """PIL.Image.Image to base64"""
    buffer = BytesIO()
    image.save(buffer, "PNG")
    x64 = buffer.getvalue()
    return 'data:image/png;base64,' + base64.b64encode(x64).decode("utf-8")
