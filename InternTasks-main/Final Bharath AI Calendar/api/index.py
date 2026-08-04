import sys
import os

# Add root directory to sys.path so main.py and all modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
