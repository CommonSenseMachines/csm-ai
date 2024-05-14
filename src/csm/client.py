import os
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

    def create_session(
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
        """
        e.g. image_url='https://via.placeholder.com/300/09f/fff.png'  
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
    
    def get_session_info(self, session_code):
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
            data = self.get_session_info(session_code)['data']
            spins = data['spins']
            selected_spin_url = spins[selected_spin_index]["image_url"]

        parameters = {
            "selected_spin_index": selected_spin_index,
            "selected_spin": selected_spin_url,
        }

        response = requests.post(
            url=os.path.join(self.base_url, "image-to-3d-sessions", "get-3d", "preview", session_code),
            json=parameters,
            headers=self._headers,
            timeout=100,
        )

        return response.json()


class CSMClient:
    def __init__(
            self,
            api_key=None,
            base_url="https://api.csm.ai:5566",
        ):
        self.backend = BackendClient(api_key=api_key, base_url=base_url)

    