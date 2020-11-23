import numpy as np
import pandas as pd
import pathlib
from typing import Union

__version__ = '1.0.0'

def parse_multina_data(filename:str):
    """ Analyzes MultiNA data by parsing it and comparing the fragments against a given target length.
            
        Args:
            filename (str): Path to MultiNA data file.
        
        Returns:
            (pandas.DataFrame): DataFrame containing parsed data.
    """
    return pd.read_csv(filename, skiprows=1, names = 
            ['number', 
             'well', 
             'name',
             'comment', 
             'peak_number', 
             'time (s)',
             'height (mV)',
             'area (mVxsec)',
             'size',
             'attribute',
             'concentration',
             'Migration Index (%)',
             'Area (mV·µm)',
             'Molarity (nmol/L)',
             'Start Index (%)',
             'End Index (%)']).replace('-', np.nan)

def analyze_multina_data(
        datafiles:dict, 
        templatefile:Union[pathlib.Path, str],
        targetfile:Union[pathlib.Path, str],
        resultfile:Union[pathlib.Path, str]='MultiNA_Result.xlsx',
        window:int=20,
    ):
    """ Analyzes MultiNA data by parsing it and comparing the fragments against a given target length.
            
        Args:
            datafiles (dict): Dictionary of datafiles, elements should be the plate identifier (key) and filepath to datafile (item).
            templatefile (pathlib.Path or str): Path to TACO template file.
            targetfile (pathlib.Path or str): Path to Excel file containing target fragment length.
            resultfile (pathlib.Path or str): Path to store result file.
            window (int): 
                Window for evalution of fragment length vs. target length. 
                E. g. with value of 20, fragments with a length of 290 to 310 would qualify for a target length of 300.
    """
    template = pd.read_excel(templatefile, index_col=0)
    target = pd.read_excel(targetfile)
    data = {key:parse_multina_data(item) for key, item in datafiles.items()}

    result = template.copy()
    true_counter = 0
    for p, playout in template.groupby('pcr_plate'):
        for r, row in playout.iterrows():    
            well_data = data[p].query('well == @row["pcr_plate_position"]').dropna(subset=['concentration'])
            target_length = target.query('construct == @row["construct_identifier"]')['fragment_length'].to_numpy()
            _tl = np.repeat(target_length, len(well_data))
            fragment_in_range = np.any(
                (well_data['concentration'].astype(float) > (_tl - (window/2))) | (well_data['concentration'].astype(float) < (_tl + (window/2)))
            )
            result.loc[r, 'pcr_result'] = fragment_in_range
            if fragment_in_range:
                true_counter += 1
    print(f'{len(template)} clones were analyzed. PCR from {true_counter} clones yielded a fragment within target length ± {window/2}.')
    result.to_excel(resultfile)
    return