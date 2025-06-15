from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Response
import logging
import traceback
from typing import List, Dict, Any, Optional, Union, Tuple
from src.shape_gen import genrate_3d_shape
from pydantic import BaseModel, Field, validator
import os
import json
from fastapi.responses import HTMLResponse, JSONResponse
import uuid

router = APIRouter()

logger = logging.getLogger(__name__)


class GenerateShapeRequest(BaseModel):
    caption: str = Field(..., description="Description of the object to generate")
    image_path: str = Field(..., description="Path to the main image")
    front_image_path: Optional[str] = Field(None, description="Path to the front view image")
    back_image_path: Optional[str] = Field(None, description="Path to the back view image")
    left_image_path: Optional[str] = Field(None, description="Path to the left view image")
    right_image_path: Optional[str] = Field(None, description="Path to the right view image")

class ShapeResponse(BaseModel):
    shape_id: str
    glb_path: Optional[str] = None
    html_content: Optional[str] = None
    model_info: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None
    number_of_faces: Optional[int] = None
    number_of_vertices: Optional[int] = None
    generation_time_ms: Optional[float] = None
    
    class Config:
        arbitrary_types_allowed = True

@router.post(
    "/generate_shape", 
    response_model=None,  # Remove the response model validation
    status_code=status.HTTP_200_OK,
    summary="Generate 3D shapes from images",
    description="Generates 3D shapes based on provided images and caption."
)
async def generate_shape(shape_data: GenerateShapeRequest):
    from src.services.firebase_service import FirebaseStorageService

    firebase_service = FirebaseStorageService()
    
    try:       

        result = await genrate_3d_shape(
            shape_data.caption, 
            shape_data.image_path,
            front_image_path=shape_data.front_image_path,
            back_image_path=shape_data.back_image_path,
            left_image_path=shape_data.left_image_path,
            right_image_path=shape_data.right_image_path
        )
        
        # Check if the result is a tuple with the expected structure
        if isinstance(result, tuple) and len(result) >= 3:
            # Extract components
            glb_info = result[0]
            html_content = result[1]
            model_stats = result[2]
            seed = result[3] if len(result) > 3 else None
            
            return_html = False 
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            firebase_result = firebase_service.upload_gltf_file(
                file_path=glb_info.get('value') if isinstance(glb_info, dict) else glb_info,
                destination_path=f"Shapes/{timestamp}_{shape_data.caption.replace(' ', '_')}.glb",
                make_public=True
            )

            # Extract the filename part from the Firebase storage URL
            storage_file_path = None
            if firebase_result:
                split_result = firebase_result.split('/')
                storage_file_path = split_result[-2] + '/' + split_result[-1]

            if not return_html:
              
                response_data = {
                    "success": True,
                    "shape_id": os.path.basename(shape_data.image_path).split('.')[0] or str(uuid.uuid4()),
                    "glb_path": glb_info.get('value') if isinstance(glb_info, dict) else None,
                    "storage_url": firebase_result if firebase_result else None,
                    "storage_file_path": storage_file_path,
                    "html_content": html_content,
                    "model_info": {
                        "model": model_stats.get('model', {}),
                        "params": model_stats.get('params', {}),
                        "statistics": {
                            "number_of_faces": model_stats.get('number_of_faces'),
                            "number_of_vertices": model_stats.get('number_of_vertices'),
                            "generation_time_ms": round(model_stats.get('time', {}).get('total', 0) * 1000) if isinstance(model_stats.get('time'), dict) else None
                        }
                    },
                    "seed": seed
                }
                
                return JSONResponse(content=response_data)
            else:
                # Return HTML viewer
                if isinstance(html_content, str) and '<iframe' in html_content:
                    return HTMLResponse(content=html_content)
                else:
                    # Fallback to JSON if HTML is not as expected
                    return JSONResponse(content={"success": True, "data": result})
        
        # Check if the result is HTML content directly
        if isinstance(result, str) and '<iframe' in result:
            return HTMLResponse(content=result)
        
        # If it's a list or dictionary, return as JSON
        if isinstance(result, (list, dict)):
            return JSONResponse(content=result)
        
        # Create a standardized response
        response_data = {
            "success": True,
            "shape_id": os.path.basename(shape_data.image_path).split('.')[0] or str(uuid.uuid4()),
            "result_type": str(type(result)),
            "data": result if isinstance(result, (dict, list, str, int, float, bool)) else str(result)
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log the full error
        error_id = uuid.uuid4().hex[:8]
        logger.error(f"Error generating shape [error_id={error_id}]: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # Return a proper HTTP error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to generate shape",
                "error_id": error_id,
                "message": str(e) if str(e) else "Unknown error in shape generation"
            }
        )
    
@router.get(
    "/download_glb",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download GLB file",
    description="Downloads the generated GLB file for the specified shape ID."
)
async def download_glb(file_path: str):
    try:
        if not file_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File path is required")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {file_path}")
        
        if not file_path.endswith('.glb'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The file is not a GLB file.")
        
        if '..' in file_path or '~' in file_path:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")
        
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as file:
            content = file.read()
        
        return Response(content=content, media_type='model/gltf-binary', headers={"Content-Disposition": f"attachment; filename={filename}"})
    except HTTPException:
        # Re-raise HTTP exceptions
        raise