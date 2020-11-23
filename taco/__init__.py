import pathlib
import pandas as pd

from . core import TacoProject, Construct, Clone

__version__ = '1.0.0'

def create_project(project_name:str):
    """ Factory for new TacoProject objects.
        
        Args:
            project_name (str): Name for the project
        
        Returns:
            taco_project (TacoProject): A new TACO project
    """

    return TacoProject(project_name)     
