from gradio_client import Client
import os
from fastapi.responses import JSONResponse, HTMLResponse
import logging
from typing import Optional, Dict, Any
from pathlib import Path


client = Client("Vuvo11/Hunyuan3D-2.0")

async def genrate_3d_shape(caption, image_path, front_image_path=None, back_image_path=None, left_image_path=None, right_image_path=None):
    # Convert string path to actual file path if it's not already
    image = str(Path(image_path))
    # Generate 3D shape using the image
    result = client.predict(
        caption=caption,
        image=image,
        mv_image_front=front_image_path,
        mv_image_back=back_image_path,
        mv_image_left=left_image_path,
        mv_image_right=right_image_path,
        steps=30,
        guidance_scale=5,
        seed=1234,
        octree_resolution=256,
        check_box_rembg=True,
        num_chunks=8000,
        randomize_seed=True,
        api_name="/shape_generation"
    )
    return result

