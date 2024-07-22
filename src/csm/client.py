import os
import time
import warnings
from urllib.request import urlretrieve
from dataclasses import dataclass
import requests
import base64
import PIL.Image
from io import BytesIO


class BackendClient:
    r"""A backend client class for raw GET/POST requests to the REST API.

    .. warning::
        This class should not be accessed directly. Instead, use :class:`CSMClient`
        to interface with the API.

    Parameters
    ----------
    api_key : str, optional
        API key for the CSM account you would like to use. If not provided,
        the environment variable :envvar:`CSM_API_KEY` is used instead.
    base_url : str
        Base url for the API. In general this should not be modified; it is 
        included only for debugging purposes.
    """
    def __init__(
            self,
            api_key=None,
            base_url="https://api.csm.ai",
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

    def _check_http_response(self, response: requests.Response):
        if not (200 <= response.status_code < 300):
            raise RuntimeError(
                f"HTTP request failed with status code {response.status_code} "
                f"({response.reason})"
            )

    # image-to-3d API
    # -------------------------------------------

    def create_image_to_3d_session(
            self,
            image_url,
            *,
            generate_preview_mesh=False,
            auto_refine=False,
            ## refine args
            creativity="lowest",
            refine_speed="fast",
            polygon_count="high_poly",
            topology="tris",
            texture_resolution=2048,
            scaled_bbox=[],
            pivot_point=[0.0, 0.0, 0.0]
        ):
        assert creativity in ["lowest", "moderate", "highest"]
        assert refine_speed in ["slow", "fast"]
        assert polygon_count in ["low_poly", "high_poly"]
        assert topology in ["tris", "quads"]
        assert 128 <= texture_resolution <= 2048

        parameters = {
            "image_url": image_url,
            "generate_preview_mesh": generate_preview_mesh,
            "creativity": creativity,
            "refine_speed": refine_speed,
            "resolution": polygon_count,
            "auto_refine": auto_refine,
            "topology": topology,
            "texture_resolution": texture_resolution,
            "manual_segmentation": False,  # TODO: implement this option
            "pivot_point": [float(s) for s in pivot_point]
        }

        if len(scaled_bbox) == 3:
            parameters["scaled_bbox"] = [float(s) for s in scaled_bbox]

        response = requests.post(
            url=f"{self.base_url}/image-to-3d-sessions",
            json=parameters,
            headers=self.headers,
        )
        self._check_http_response(response)  # expected=201

        return response.json()

    def get_image_to_3d_session_info(self, session_code):
        response = requests.get(
            url=f"{self.base_url}/image-to-3d-sessions/{session_code}",
            headers=self.headers,
        )
        self._check_http_response(response)  # expected=200

        return response.json()
    
    def get_3d_refine(self, session_code, scaled_bbox=[], pivot_point=[0.0, 0.0, 0.0]):
        parameters = {"pivot_point": [s for s in pivot_point]}
        if len(scaled_bbox) == 3:
            parameters["scaled_bbox"] = [float(s) for s in scaled_bbox]
        response = requests.post(
            url=f"{self.base_url}/image-to-3d-sessions/get-3d/refine/{session_code}",
            json=parameters,
            headers=self.headers,
        )

        return response.json()
    
    def get_3d_preview(self, session_code, spin_url=None, scaled_bbox=[], pivot_point=[0.0, 0.0, 0.0]):
        selected_spin_index = 0

        if spin_url is None:
            result = self.get_image_to_3d_session_info(session_code)
            spin_url = result['data']['spins'][selected_spin_index]["image_url"]

        parameters = {
            "selected_spin_index": selected_spin_index,
            "selected_spin": spin_url,
            "pivot_point": [s for s in pivot_point]
        }

        if len(scaled_bbox) == 3:
            parameters["scaled_bbox"] = [float(s) for s in scaled_bbox]

        response = requests.post(
            url=f"{self.base_url}/image-to-3d-sessions/get-3d/preview/{session_code}",
            json=parameters,
            headers=self.headers,
            timeout=100,
        )
        self._check_http_response(response)  # expected=200

        return response.json()

    # text-to-image API methods
    # -------------------------------------------

    def create_text_to_image_session(
            self,
            prompt,
            style_id="",
            guidance=6,
        ):
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
        self._check_http_response(response)

        return response.json()

    def get_text_to_image_session_info(self, session_code):
        response = requests.get(
            url=f"{self.base_url}/tti-sessions/{session_code}",
            headers=self.headers,
        )
        self._check_http_response(response)

        return response.json()


@dataclass
class ImageTo3DResult:
    r"""
    Output class for image-to-3d generation.

    Parameters
    ----------
    session_code : str
        The image-to-3d session code.
    mesh_path : str
        Local path of the generated mesh file.
    """

    session_code: str
    mesh_path: str


@dataclass
class TextTo3DResult:
    r"""
    Output class for text-to-3d generation.

    Parameters
    ----------
    session_code : str
        The image-to-3d session code.
    mesh_path : str
        Local path of the generated mesh file.
    image_path : str
        Local path of the image generated as part of text-to-3d.
    """

    session_code: str
    mesh_path: str
    image_path: str


class CSMClient:
    r"""Core client utility for accessing the CSM API.

    Parameters
    ----------
    api_key : str, optional
        API key for the CSM account you would like to use. If not provided,
        the environment variable :envvar:`CSM_API_KEY` is used instead.
    base_url : str
        Base url for the API. In general this should not be modified; it is 
        included only for debugging purposes.
    """
    def __init__(
            self,
            api_key=None,
            base_url="https://api.csm.ai",
        ):
        self.backend = BackendClient(api_key=api_key, base_url=base_url)

    def _handle_image_input(self, image):
        if isinstance(image, str):
            if os.path.isfile(image):  # local file path
                image_path = image
                pil_image = PIL.Image.open(image_path)
            else:  # URL for a web file
                image_url = image
                return image_url  # TODO: verify that this is a valid URL
        elif isinstance(image, PIL.Image.Image):
            pil_image = image
        else:
            raise ValueError(f"Encountered unexpected type for the input image.")
        
        return pil_image_to_x64(pil_image)

    def image_to_3d(
            self,
            image,
            *,
            generate_spin_video=False,
            mesh_format='obj',
            output='./',
            timeout=200,
            verbose=True,
            scaled_bbox=[],
            pivot_point=[0.0, 0.0, 0.0],
            refine_speed="fast"
        ):
        r"""Generate a 3D mesh from an image.

        The input image can be provided as a URL, a local path, or a :class:`PIL.Image.Image`.

        Parameters
        ----------
        image : str or PIL.Image.Image
            The input image. May be provided as a url, a local path, or a
            :class:`PIL.Image.Image` instance.

        Returns
        -------
        ImageTo3DResult
            Result object. Contains the local path of the generated mesh file.
        """
        if generate_spin_video:
            warnings.warn(
                "The option `generate_spin_video=True` is deprecated and will be removed "
                "in a future release", DeprecationWarning)

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
            generate_preview_mesh=not generate_spin_video,
            auto_refine=False,
            scaled_bbox=scaled_bbox,
            pivot_point=pivot_point,
            refine_speed=refine_speed
        )

        status = result['data']['status']
        if (
            (generate_spin_video and status not in ["spin_generate_processing", "spin_generate_done"]) or
            (not generate_spin_video and status not in ["training_preview", "preview_done"])
            ):
            raise RuntimeError(f"Image-to-3d session creation failed (status='{status}')")

        session_code = result['data']['session_code']

        step_label = "spin generation" if generate_spin_video else "mesh generation"

        if verbose:
            print(f'[INFO] Image-to-3d session created ({session_code})')

        if generate_spin_video:
            if verbose:
                print(f'[INFO] Running preview {step_label}...')

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
                    raise RuntimeError(f"Preview {step_label} failed")
                elif status != 'spin_generate_processing':
                    raise RuntimeError(f"Unexpected error during preview {step_label} (status='{status}')")
                run_time = time.time() - start_time
                if run_time >= timeout:
                    raise RuntimeError(f"Preview {step_label} timed out")
            
            if verbose:
                print(f'[INFO] Preview {step_label} completed in {run_time:.1f}s')

            spin_url = result['data']['spins'][0]["image_url"]

            # launch preview mesh export
            result = self.backend.get_3d_preview(
                session_code,
                spin_url=spin_url,
                scaled_bbox=scaled_bbox,
                pivot_point=pivot_point
            )
            step_label = "mesh export"

        if verbose:
            print(f'[INFO] Running preview {step_label}...')

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
                raise RuntimeError(f"Preview {step_label} failed.")
            elif status != 'training_preview':
                raise RuntimeError(f"Unexpected error during preview {step_label} (status='{status}')")
            run_time = time.time() - start_time
            if run_time >= timeout:
                raise RuntimeError(f"Preview {step_label} timed out")
            
        if verbose:
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

        return ImageTo3DResult(session_code=session_code, mesh_path=mesh_path)

    def text_to_3d(
            self,
            prompt,
            *,
            style_id="",
            guidance=6,
            generate_spin_video=False,
            mesh_format='obj',
            output='./',
            timeout=200,
            verbose=True,
            scaled_bbox=[],
            pivot_point=[0.0, 0.0, 0.0],
            refine_speed="fast"
        ):
        r"""Generate a 3D mesh from a text prompt.

        Parameters
        ----------
        prompt : str
            The input text prompt.

        Returns
        -------
        TextTo3DResult
            Result object. Contains the local path of the generated mesh file,
            as well as the image that was generated as part of the pipeline.
        """
        os.makedirs(output, exist_ok=True)

        # initialize text-to-image session
        result = self.backend.create_text_to_image_session(
            prompt,
            style_id=style_id,
            guidance=guidance,
        )

        status = result['data']['status']
        if status != "processing" and status != "completed":
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
        i23 = self.image_to_3d(
            image_url,
            generate_spin_video=generate_spin_video,
            mesh_format=mesh_format,
            output=output,
            timeout=timeout,
            verbose=verbose,
            scaled_bbox=scaled_bbox,
            pivot_point=pivot_point,
            refine_speed=refine_speed
        )

        return TextTo3DResult(session_code=i23.session_code, mesh_path=i23.mesh_path, image_path=image_path)


def pil_image_to_x64(image: PIL.Image.Image) -> str:
    """PIL.Image.Image to base64"""
    buffer = BytesIO()
    image.save(buffer, "PNG")
    x64 = buffer.getvalue()
    return 'data:image/png;base64,' + base64.b64encode(x64).decode("utf-8")
