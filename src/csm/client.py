import os
import time
import warnings
from urllib.request import urlretrieve
from urllib.parse import urlparse
from dataclasses import dataclass
import requests
import base64
import PIL.Image
from io import BytesIO


class BackendClient:
    """A backend client class for raw GET/POST requests to the REST API.

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
        ) -> None:
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
        """Constructs and returns the HTTP headers required for API requests."""
        return {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }

    def _check_http_response(self, response: requests.Response) -> None:
        """Validates the HTTP response for successful status codes.

        Raises an error if the response indicates a failed request.
        
        Parameters
        ----------
        response : requests.Response
            The HTTP response object to check.
        """
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
            **kwargs
        ) -> dict:
        """Creates an image-to-3D conversion session.

        Parameters
        ----------
        image_url : str
            URL of the image to convert into a 3D model.
        **kwargs : dict, optional
            Additional parameters for customizing the image-to-3D process.
            For a complete list of supported options, see the REST API documentation:
            `Session Parameters <https://docs.csm.ai/image-to-3d/create-session>`_.
        
        Returns
        -------
        dict
            The response from the API containing session details.
        """

        parameters = {
            "image_url": image_url,
            "manual_segmentation": False,  # TODO: implement this option
            **kwargs
        }

        response = requests.post(
            url=f"{self.base_url}/image-to-3d-sessions",
            json=parameters,
            headers=self.headers,
        )
        self._check_http_response(response)  # expected=201

        return response.json()

    def get_image_to_3d_session_info(self, session_code) -> dict:
        """Fetches information about an existing image-to-3D session.

        Parameters
        ----------
        session_code : str
            The session code of the image-to-3D session.
        
        Returns
        -------
        dict
            The response from the API containing session details.
        """
        response = requests.get(
            url=f"{self.base_url}/image-to-3d-sessions/{session_code}",
            headers=self.headers,
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
        ) -> dict:
        """Creates a text-to-image session.

        Parameters
        ----------
        prompt : str
            The text prompt for generating an image.
        
        Returns
        -------
        dict
            The response from the API with session details.
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
        self._check_http_response(response)

        return response.json()

    def get_text_to_image_session_info(self, session_code: str) -> dict:
        """Fetches information for an existing text-to-image session.

        Parameters
        ----------
        session_code : str
            The session code of the text-to-image session.
        
        Returns
        -------
        dict
            The response from the API with session details.
        """
        response = requests.get(
            url=f"{self.base_url}/tti-sessions/{session_code}",
            headers=self.headers,
        )
        self._check_http_response(response)

        return response.json()


@dataclass
class ImageTo3DResult:
    """Output class for image-to-3d generation.

    Parameters
    ----------
    mesh_path : str
        Local path of the generated mesh file.
    session_code : str
        The image-to-3d session code.
    session_data : dict
        Full image-to-3d session data returned by the REST API
    """
    mesh_path: str
    session_code: str
    session_data: dict


@dataclass
class TextToImageResult:
    """Output class for text-to-3d generation.

    Parameters
    ----------
    image_path : str
        Local path of the generated image.
    session_code : str
        The text-to-image session code.
    session_data : dict
        Full text-to-image session data returned by the REST API
    """
    image_path: str
    session_code: str
    session_data: dict


@dataclass
class TextTo3DResult:
    """Output class for text-to-3d generation.

    Parameters
    ----------
    mesh_path : str
        Local path of the generated mesh file.
    image_path : str
        Local path of the image generated as part of text-to-3d.
    session_code : str
        The image-to-3d session code.
    session_data : dict
        Full image-to-3d session data returned by the REST API
    """
    mesh_path: str
    image_path: str
    session_code: str
    session_data: dict


class CSMClient:
    """Core client utility for accessing the CSM API.

    Parameters
    ----------
    api_key : str, optional
        API key for the CSM account you would like to use. If not provided,
        the environment variable :envvar:`CSM_API_KEY` is used instead.
    base_url : str
        Base url for the API. In general this should not be modified; it is 
        included only for debugging purposes.
    verbose : bool
        If True, the client outputs detailed progress information. Verbosity
        can also be specified per-session with method argument `verbose`.
        Defaults to True.
    """
    def __init__(
            self,
            api_key=None,
            base_url="https://api.csm.ai",
            verbose=True,
        ) -> None:
        self.backend = BackendClient(api_key=api_key, base_url=base_url)
        self.verbose = verbose
        self._set_verbosity()

    def _set_verbosity(self, verbose=None):
        self._verbose = self.verbose if verbose is None else verbose

    def _log(self, message):
        if self._verbose:
            #print(f'[INFO] {message}')
            print(f'[{type(self).__name__}] {message}')

    def _handle_image_input(self, image) -> str:
        """Handles image input by converting it to a base64-encoded string.

        Parameters
        ----------
        image : str or PIL.Image.Image
            The input image, either as a file path, URL, or PIL Image.

        Returns
        -------
        str or PIL.Image.Image
            The base64 encoded string if local or PIL image, else image URL.
        """
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

    def start_image_to_3d(
        self,
        image,
        *,
        verbose=None,
        **kwargs
    ) -> str:
        """Start an image-to-3d session and return the session code.

        Parameters
        ----------
        image : str or PIL.Image.Image
            The input image. May be provided as a URL, a local file path, or a
            :class:`PIL.Image.Image` instance.
        verbose : bool, optional
            If True, outputs detailed progress information. Defaults to `self.verbose`.
        **kwargs : dict, optional
            Additional parameters for customizing the image-to-3D process.
            For a complete list of supported options, see the REST API documentation:
            `Session Parameters <https://docs.csm.ai/image-to-3d/create-session>`_.

        Returns
        -------
        str
            The image-to-3d session code.
        """
        self._set_verbosity(verbose)

        _deprecated_args = [
            'generate_spin_video',
            'preview_mesh',
            'refine_speed',
            'preview_model',
        ]
        for arg in _deprecated_args:
            if kwargs.pop(arg, None) is not None:
                warnings.warn(
                    f"Argument `{arg}` has been deprecated and is no longer used.",
                    DeprecationWarning
                )

        image_url = self._handle_image_input(image)

        # initialize session
        result = self.backend.create_image_to_3d_session(
            image_url,
            **kwargs
        )

        status = result['data']['session_status']
        if status == 'failed':
            raise RuntimeError(f"Image-to-3d session creation failed (session status='{status}')")

        session_code = result['data']['session_code']
        self._log(f'Image-to-3d session created ({session_code})')

        return session_code

    def poll_image_to_3d(
        self,
        session_code,
        *,
        mesh_format='glb',
        output='./',
        timeout=1000,
        poll_interval=5,
        verbose=None,
    ) -> ImageTo3DResult:
        """Poll an image-to-3d session and return the result when it arrives.

        Parameters
        ----------
        session_code : str
            The image-to-3d session code.
        mesh_format : str, optional
            The format of the output 3D mesh file. Choices are ['obj', 'glb', 'fbx', 'usdz'].
            Defaults to 'glb'.
        output : str, optional
            The directory path where output files will be saved.
        timeout : int, optional
            The maximum time (in seconds) to wait for the 3D mesh generation.
        poll_interval : int
            Time to wait (in seconds) between iterations while polling for a result.
        verbose : bool, optional
            If True, outputs detailed progress information. Defaults to `self.verbose`.

        Returns
        -------
        ImageTo3DResult
            Result object containing the local path of the generated mesh file and session code.
        """
        self._set_verbosity(verbose)

        self._log(f'Running image-to-3d...')

        # poll session until complete
        start_time = time.time()
        run_time = 0.
        while run_time < timeout:
            # Get latest session info
            result = self.backend.get_image_to_3d_session_info(session_code)
            status = result['data']['session_status']
            percent_done = result['data'].get('percent_done', 'N/A')
            self._log(f'{session_code}: status="{status}", progress={percent_done}%')

            if status == 'complete':
                self._log(f'image-to-3d completed in {run_time:.1f}s')
                break

            elif status == 'failed':
                raise RuntimeError(f"image-to-3d failed.")

            # TODO: check remaining status values?
            #assert status in ['queued', 'in_progress']

            # Wait `poll_interval` seconds and repeat
            time.sleep(poll_interval)
            run_time = time.time() - start_time

        else:
            raise TimeoutError(f"image-to-3d timed out")

        # initialize output directory
        os.makedirs(output, exist_ok=True)

        # check mesh format
        mesh_format = mesh_format.lower()
        allowed_formats = ['obj', 'zip', 'glb', 'fbx', 'usdz']
        if mesh_format not in allowed_formats:
            raise ValueError(
                f"Unexpected mesh_format value ('{mesh_format}'). Please choose "
                f"from options {allowed_formats}."
            )

        # download mesh file based on the requested format
        mesh_url = result['data'][f'mesh_url_{mesh_format}']
        #mesh_file = f'mesh.{mesh_format}'
        mesh_file = os.path.basename(urlparse(mesh_url).path)
        mesh_path = os.path.join(output, mesh_file)  # TODO: os.path.abspath ?
        urlretrieve(mesh_url, mesh_path)

        i23_result = ImageTo3DResult(
            mesh_path=mesh_path,
            session_code=session_code,
            session_data=result['data'],
        )

        return i23_result

    def image_to_3d(
        self,
        image,
        *,
        mesh_format='glb',
        output='./',
        timeout=1000,
        poll_interval=5,
        verbose=None,
        **kwargs
    ) -> ImageTo3DResult:
        """
        Generate a 3D mesh from an image.

        The input image can be provided as a URL, a local path, or a :class:`PIL.Image.Image`.

        Parameters
        ----------
        image : str or PIL.Image.Image
            The input image. May be provided as a URL, a local file path, or a 
            :class:`PIL.Image.Image` instance.
        mesh_format : str, optional
            The format of the output 3D mesh file. Choices are ['obj', 'glb', 'fbx', 'usdz'].
            Defaults to 'glb'.
        output : str, optional
            The directory path where output files will be saved.
        timeout : int, optional
            The maximum time (in seconds) to wait for the 3D mesh generation.
        poll_interval : int
            Time to wait (in seconds) between iterations while polling for a result.
        verbose : bool, optional
            If True, outputs detailed progress information. Defaults to `self.verbose`.
        **kwargs : dict, optional
            Additional parameters for customizing the image-to-3D process.
            For a complete list of supported options, see the REST API documentation:
            `Session Parameters <https://docs.csm.ai/image-to-3d/create-session>`_.

        Returns
        -------
        ImageTo3DResult
            Result object containing the local path of the generated mesh file and session code.
        """
        self._set_verbosity(verbose)

        session_code = self.start_image_to_3d(
            image,
            verbose=verbose,
            **kwargs
        )

        i23_result = self.poll_image_to_3d(
            session_code,
            mesh_format=mesh_format,
            output=output,
            timeout=timeout,
            poll_interval=poll_interval,
            verbose=verbose,
        )

        return i23_result

    def start_text_to_image(
            self,
            prompt,
            *,
            style_id="",
            guidance=6,
            verbose=None,
        ) -> str:
        """Start a text-to-image session and return the session code.

        Parameters
        ----------
        prompt : str
            The input text prompt to generate an image based on text description.
        style_id : str, optional
            The style ID that influences the visual characteristics of the generated model.
            Defaults to an empty string, meaning no specific style is applied.
        guidance : int, optional
            A parameter that adjusts guidance strength, affecting how closely
            the generation follows the input text. Default is 6.
        verbose : bool, optional
            If True, outputs detailed progress information. Defaults to `self.verbose`.

        Returns
        -------
        str
            The text-to-image session code.
        """
        self._set_verbosity(verbose)

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
        self._log(f'Text-to-image session created ({session_code})')

        return session_code

    def poll_text_to_image(
            self,
            session_code,
            *,
            output='./',
            timeout=1000,
            poll_interval=5,
            verbose=None,
        ) -> TextToImageResult:
        """Poll a text-to-image session and return the result when it arrives.

        Parameters
        ----------
        session_code : str
            The text-to-image session code.
        output : str, optional
            The directory path where output files will be saved. Defaults to
            the current directory.
        timeout : int, optional
            The maximum time (in seconds) to wait for the 3D mesh generation.
        poll_interval : int
            Time to wait (in seconds) between iterations while polling for a result.
        verbose : bool, optional
            If True, outputs detailed progress information. Defaults to `self.verbose`.

        Returns
        -------
        TextToImageResult
            Result object containing the local path of the generated image and session code.
        """
        self._set_verbosity(verbose)

        self._log(f'Running text-to-image...')

        # poll session until complete
        start_time = time.time()
        run_time = 0.
        while run_time < timeout:
            # Get latest session info
            result = self.backend.get_text_to_image_session_info(session_code)
            status = result['data']['status']

            if status == 'completed':
                self._log(f'text-to-image completed in {run_time:.1f}s')
                break

            elif status != 'processing':
                raise RuntimeError(
                    f"Unexpected error during text-to-image generation (status='{status}')")

            # Wait `poll_interval` seconds and repeat
            time.sleep(poll_interval)
            run_time = time.time() - start_time

        else:
            raise TimeoutError("text-to-image timed out")

        # access the image URL
        image_url = result['data']['image_url']

        # download image
        image_path = os.path.join(output, 'image.png')
        urlretrieve(image_url, image_path)

        t2i_result = TextToImageResult(
            image_path=image_path,
            session_code=session_code,
            session_data=result['data'],
        )

        return t2i_result

    def text_to_3d(
            self,
            prompt,
            *,
            style_id="",
            guidance=6,
            mesh_format='glb',
            output='./',
            timeout=1000,
            poll_interval=5,
            verbose=None,
            **kwargs
        ) -> TextTo3DResult:
        """Generate a 3D mesh from a text prompt.

        Parameters
        ----------
        prompt : str
            The input text prompt to generate a 3D model based on text description.
        style_id : str, optional
            The style ID that influences the visual characteristics of the generated model.
            Defaults to an empty string, meaning no specific style is applied.
        guidance : int, optional
            A parameter that adjusts guidance strength, affecting how closely 
            the generation follows the input text. Default is 6.
        mesh_format : str, optional
            The format of the output 3D mesh file. Choices are ['obj', 'glb', 'fbx', 'usdz'].
            Defaults to 'glb'.
        output : str, optional
            The directory path where output files (mesh and video, if generated) 
            will be saved. Defaults to the current directory.
        timeout : int, optional
            The maximum time (in seconds) to wait for the 3D mesh generation. 
        poll_interval : int
            Time to wait (in seconds) between iterations while polling for a result.
        verbose : bool, optional
            If True, outputs detailed progress information. Defaults to `self.verbose`.
        **kwargs : dict, optional
            Additional parameters for customizing the image-to-3D process.
            For a complete list of supported options, see the REST API documentation:
            `Session Parameters <https://docs.csm.ai/image-to-3d/create-session>`_.

        Returns
        -------
        TextTo3DResult
            Result object. Contains the local path of the generated mesh file,
            as well as the image generated as part of the pipeline, and session code.
        """
        self._set_verbosity(verbose)

        session_code = self.start_text_to_image(
            prompt,
            style_id=style_id,
            guidance=guidance,
            verbose=verbose,
        )

        t2i_result = self.poll_text_to_image(
            session_code,
            output=output,
            timeout=timeout,
            poll_interval=poll_interval,
            verbose=verbose,
        )
        image_path = t2i_result.image_path

        # launch image-to-3d
        i23_result = self.image_to_3d(
            image_path,
            mesh_format=mesh_format,
            output=output,
            timeout=timeout,
            poll_interval=poll_interval,
            **kwargs
        )

        t23_result = TextTo3DResult(
            mesh_path=i23_result.mesh_path,
            image_path=image_path,
            session_code=i23_result.session_code,
            session_data=i23_result.session_data,
        )

        return t23_result


def pil_image_to_x64(image: PIL.Image.Image) -> str:
    """Converts a PIL.Image.Image to a base64-encoded PNG string.

    Parameters
    ----------
    image : PIL.Image.Image
        The image to convert.

    Returns
    -------
    str
        The base64 encoded image string.
    """
    buffer = BytesIO()
    image.save(buffer, "PNG")
    x64 = buffer.getvalue()
    return 'data:image/png;base64,' + base64.b64encode(x64).decode("utf-8")
