from gradio_client import Client, handle_file
from pathlib import Path
import os

# Ensure the environment variable for Hugging Face token is set
hf_token = os.getenv('HF_TOKEN')

model_url1 = 'tencent/Hunyuan3D-2.1'
model_url2 = 'Vuvo11/Hunyuan3D-2.1'

client = Client(model_url2, hf_token=hf_token)

async def genrate_3d_shape(caption, image_path, front_image_path=None, back_image_path=None, left_image_path=None, right_image_path=None):
    # Convert string path to actual file path if it's not already
    image = handle_file(image_path)

    # Generate 3D shape using the image
    result = client.predict(
                image=image,
                mv_image_front=None,
                mv_image_back=None,
                mv_image_left=None,
                mv_image_right=None,
                steps=30,
                guidance_scale=5,
                seed=1234,
                octree_resolution=256,
                check_box_rembg=True,
                num_chunks=8000,
                randomize_seed=True,
                api_name="/generation_all"
    )
    return result

