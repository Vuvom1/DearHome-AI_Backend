import asyncio
import os
import logging
import traceback
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from src.database.init_db import init_db
from src.database.db_connection import create_session

from src.handlers import variant_sync_handler
from src.routers.chat_router import router as chat_router
from src.routers.shape_gen_router import router as shape_gen_router
from src.routers.virtual_room_router import router as virtual_room_router

from src.handlers.product_sync_handler import product_sync_handler
from src.handlers.variant_sync_handler import variant_sync_handler
from src.handlers.promotion_sync_handler import promotion_sync_handler
from src.handlers.order_sync_handler import order_sync_handler


# Set up structured logging following Azure best practices
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

async def setup_product_sync_handler():
    """Initialize the product sync handler"""
    logger.info("Setting up product sync handler...")
    try:
        await product_sync_handler.initialize()
        logger.info("Product sync handler initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing product sync handler: {str(e)}")
        logger.debug(traceback.format_exc())
        return False
    
async def setup_variant_sync_handler():
    """Initialize the variant sync handler"""
    logger.info("Setting up variant sync handler...")
    try:
        await variant_sync_handler.initialize()
        logger.info("Variant sync handler initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing variant sync handler: {str(e)}")
        logger.debug(traceback.format_exc())
        return False
    
async def setup_promotion_sync_handler():
    """Initialize the promotion sync handler"""
    logger.info("Setting up promotion sync handler...")
    try:
        await promotion_sync_handler.initialize()
        logger.info("Promotion sync handler initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing promotion sync handler: {str(e)}")
        logger.debug(traceback.format_exc())
        return False    
    
async def setup_order_sync_handler():
    """Initialize the order sync handler"""
    logger.info("Setting up order sync handler...")
    try:
        await order_sync_handler.initialize()
        logger.info("Order sync handler initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing order sync handler: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application startup and shutdown"""
    # Startup
    logger.info("Starting up application...")
    try:
        # Initialize product handlers
        product_handlers = await setup_product_sync_handler()
        if not product_handlers:
            logger.error("Failed to initialize product sync handler")
            raise RuntimeError("Product sync handler initialization failed")

        # Initialize variant handlers
        variant_handlers = await setup_variant_sync_handler()
        if not variant_handlers:
            logger.error("Failed to initialize variant sync handler")
            raise RuntimeError("Variant sync handler initialization failed")
        
        # Initialize promotion handlers
        promotion_handlers = await setup_promotion_sync_handler()
        if not promotion_handlers:
            logger.error("Failed to initialize promotion sync handler")
            raise RuntimeError("Promotion sync handler initialization failed")
        
        # Initialize order handlers
        order_handlers = await setup_order_sync_handler()
        if not order_handlers:
            logger.error("Failed to initialize order sync handler")
            raise RuntimeError("Order sync handler initialization failed")

        logger.info("Application startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
        
    finally:
        # Shutdown
        logger.info("Shutting down application...")
        try:
            # Clean up product handler
            if hasattr(app.state, "product_handler"):
                await app.state.product_handler.shutdown()
                
            # Close database connections
            if hasattr(app.state, "db"):
                app.state.db.close()
                
            logger.info("Application shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Business Interior Chat Assistant",
    description="API for the Business Interior Chat Assistant",
    version="1.0.0",
    docs_url="/api/docs",  
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Enable CORS with Azure best practices for security
allowed_origins = [
    "*",  # Allow all origins for development; restrict in production
]

if os.getenv("WEBSITE_HOSTNAME"):
    allowed_origins.append(f"https://{os.getenv('WEBSITE_HOSTNAME')}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  
    allow_headers=["*"],  
    max_age=600,  
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Generate request ID if not provided (Azure Application Insights compatible)
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    # Set correlation ID for this request context
    request.state.request_id = request_id
    
    # Add request ID and execute request
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    # Log request completion with performance data (Azure Monitor optimized format)
    logger.info(
        f"Request {request.method} {request.url.path} completed in {process_time:.4f}s "
        f"with status {response.status_code} [request_id={request_id}]"
    )
    
    return response

def get_db():
    session_result = create_session()
    if not session_result.get("success"):
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable"
        )
    
    session = session_result["session"]
    try:
        yield session
    finally:
        session.close()

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(shape_gen_router, prefix="/api", tags=["shape_gen"])
app.include_router(virtual_room_router, prefix="/api/virtual_room", tags=["virtual_room"])



# Update FastAPI initialization to use lifespan


# Remove the old startup event handler
# @app.on_event("startup") is now replaced by the lifespan context manager

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Configure for different deployment environments
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    
    # Use reload in development only (Azure best practice)
    reload = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    # Start the API server
    uvicorn.run(
        "app:app", 
        host=host, 
        port=port, 
        reload=reload,
        log_level="info"
    )