"""
Business Interior Design Chatbot - Main Package
Implements Azure best practices for scalable, secure AI applications
"""

import sys
from pathlib import Path
import src

# Configure Python path properly (Azure best practice)
# Instead of using sys.path.append which can cause conflicts
# Use the more reliable method with pathlib
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Package metadata (Azure best practice for versioning)
__version__ = '0.1.0'
__author__ = 'Business Interior Team'

