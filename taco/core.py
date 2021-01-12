"""Specifices base classes"""

import pandas as pd
import pathlib
from typing import TypedDict

from . utils import NoClonesError, NoConstructsError

class TacoProject():
    """Holds project data"""
    def __init__(self, project_name:str):
        self._project_name = project_name
        self.constructs = list()

    @property
    def project_name(self) -> str:
        """Contains the name of the project."""
        return self._project_name

    def generate_construct_template(self, filename:str=None, properties:list=None):
        """ Generates an Excel file to be used as a template for construct data input.
            
            Args:
                filename (str): Filename for the input template. If None, project name + '_constructs.xlsx' will be used.
                properties (list): Properties associated with constructs. If None, ['property_1', 'property_2', 'property_3'] will be used.

            Raises:
                FileExistsError: If the file already exists.
        """
        if properties == None:
            template = pd.DataFrame(columns=['identifier', 'property_1', 'property_2', 'property_3'])
        else:
            template = pd.DataFrame(columns=['identifier'] + properties)

        if filename == None:
            _filename = pathlib.Path(f'{self.project_name}_constructs.xlsx')
        else:
            _filename = pathlib.Path(filename)

        if _filename.exists():
            raise FileExistsError('File already exists. Please delete the old template or choose a different file name.')
        else:
            template.to_excel(_filename, index=False)

    def read_construct_input(self, filename:str=None):
        """ Reads an Excel file containing a list of constructs.
            
            Args:
                filename (str): Filename for the input. If None, project name + '_constructs.xlsx' will be used.
        """
        if filename == None:
            _filename = f'{self.project_name}_constructs.xlsx'
        else:
            _filename = filename

        data = pd.read_excel(_filename, index_col=0).to_dict('index')
        unique_counter=0
        duplicate_counter=0
        existing_ids = {x['identifier'] for x in self.constructs}

        for identifier, properties in data.items():
            if identifier in existing_ids:
                duplicate_counter+=1
            else:
                unique_counter += 1

                new_construct: Construct = {'identifier': identifier, 'properties': properties, 'clones': []}
                self.constructs.append(new_construct)

        if unique_counter:
            print(f'{unique_counter} constructs added to the project. {duplicate_counter} duplicates were skipped.')
        else:
            raise NoConstructsError('No new constructs found in file')

    def generate_transformation_template(self, filename:str=None):
        """ Generates an Excel file to be used as a template for data input from a transformation round.
            
            Args:
                filename (str): Filename for the input template. If None, project name + '_transformation_results.xlsx' will be used.

            Raises:
                FileExistsError: If the file already exists.
        """
        if filename == None:
            _filename = pathlib.Path(f'{self.project_name}_transformation_results.xlsx')
        else:
            _filename = pathlib.Path(filename)

        if _filename.exists():
            raise FileExistsError('File already exists. Please delete the old template or choose a different file name.')

        template = pd.DataFrame(columns=['identifier', 'agar_plate_number', 'agar_plate_position', 'number_of_clones'])
        template['identifier'] = [construct['identifier'] for construct in self.constructs]
        template.to_excel(_filename, index=False)

    def read_transformation_input(self, filename:str=None):
        """ Reads an Excel file containing a list of transformed constructs.
            
            Args:
                filename (str): Filename for the input. If None, project name + '_transformation_results.xlsx' will be used.
        """
        if filename == None:
            _filename = f'{self.project_name}_transformation_results.xlsx'
        else:
            _filename = filename

        data = pd.read_excel(_filename)
        
        clone_counter = 0
        for _, row in data.iterrows():   
            for construct in self.constructs:
                if row['identifier'] == construct['identifier']:
                    break
            else:
                raise ValueError(f'Could not find {row["identifier"]} in list of constructs.')

            clones = []
            for i in range(1, row['number_of_clones'] + 1):
                new_clone: Clone = {
                    'identifier': f"{row['identifier']}_{i}",
                    'agar_plate_number': row['agar_plate_number'],
                    'agar_plate_position': row['agar_plate_position'],
                    'pcr_result': None,
                    'seq_result': None,
                    'storage_plate_number': None,
                    'storage_plate_position': None,
                }
                clones.append(new_clone)
                clone_counter += 1

            construct['clones'] = clones
    
        print(f'{clone_counter} clones were added to the project.')

    def generate_pcr_template(self, filename:str=None, max_clones:int=None, use_mtp=False):
        """ Generates an Excel file to be used as a template for PCR data input.
            
            Args:
                max_clones (int): Maximum number of clones to test. If None, all clones of each construct are choosen. 
                filename (str): Filename for the input template. If None, project name + '_pcr_results.xlsx' will be used.
                use_mtp (boolean): If true, template will have additional columns for 96 well PCR plates and positions
            
            Raises:
                FileExistsError: If the file already exists.
                NoClonesError: If non of the constructs has any clones.
        """
        if filename == None:
            _filename = pathlib.Path(f'{self.project_name}_pcr_results.xlsx')
        else:
            _filename = pathlib.Path(filename)

        if _filename.exists():
            raise FileExistsError('File already exists. Please delete the old template or choose a different file name.')

        pcr_counter = 1
        pcr_plate_counter = 1
        pcr_position_counter = 1
        pcr_position_mapping = dict(zip(range(1,97), [f'{l}{n}' for l in 'ABCDEFGH' for n in range(1,13)]))
        all_clone_counter = 0

        collection = []
        for construct in self.constructs:
            clone_counter = 0
            for clone in construct['clones']:
                new_entry = {
                    'construct_identifier': construct['identifier'],
                    'clone_identifier': clone['identifier'],
                    'agar_plate_number': clone['agar_plate_number'],
                    'agar_plate_position': clone['agar_plate_position'],
                    'pcr_identifier': pcr_counter,
                }
                if use_mtp:
                    new_entry.update({
                        'pcr_plate': pcr_plate_counter,
                        'pcr_plate_position': pcr_position_mapping[pcr_position_counter],
                    })
                new_entry.update({'pcr_result': None})
                collection.append(new_entry)
                pcr_counter += 1
                clone_counter += 1
                all_clone_counter += 1

                if pcr_position_counter == 96:
                    pcr_position_counter = 1
                    pcr_plate_counter += 1
                else:
                    pcr_position_counter += 1

                if max_clones and (clone_counter >= max_clones):
                    break
        
        if all_clone_counter == 0:
            raise NoClonesError('There are no clones in your project.')

        template = pd.DataFrame(collection)
        template.to_excel(_filename)

    def read_pcr_input(self, filename:str=None):
        """ Reads an Excel file containing results from colony PCR.
            
            Args:
                filename (str): Filename for the input. If None, project name + '_pcr_results.xlsx' will be used.

        """
        if filename == None:
            _filename = f'{self.project_name}_pcr_results.xlsx'
        else:
            _filename = filename

        data = pd.read_excel(_filename)
        counter = 0
        for _, row in data.iterrows():
            for construct in self.constructs:
                for clone in construct['clones']:
                    if row['clone_identifier'] == clone['identifier']:
                        break
                else:
                    clone = None
                if not clone is None:
                    break
            else:
                raise ValueError(f'Clone {row["clone_identifier"]} could not be found.')

            if row['pcr_result'] == 'y' or row['pcr_result'] == True:
                clone['pcr_result'] = 'success'
                counter += 1
            elif row['pcr_result'] == 'n' or row['pcr_result'] == False:
                clone['pcr_result'] = 'fail'
                counter += 1

        print(f'PCR data for {counter} clones added')

    def generate_seq_template(self, only_with_positive_pcr:bool=True, max_clones:int=None,  filename:str=None):
        """ Generates an Excel file to be used as a template for SEQ data input.
            
            Args:
                only_with_positive_pcr (bool): If True, only clones with a positive PCR results are considered.
                max_clones (int): Maximum number of clones to test. If None, all clones of each construct are potentially choosen.  
                filename (str): Filename for the input template. If None, project name + '_seq_results.xlsx' will be used.
            
            Raises:
                FileExistsError: If the file already exists.
                NoClonesError: If non of the constructs has any clones.
        """
        if filename == None:
            _filename = pathlib.Path(f'{self.project_name}_seq_results.xlsx')
        else:
            _filename = pathlib.Path(filename)

        if _filename.exists():
            raise FileExistsError('File already exists. Please delete the old template or choose a different file name.')

        seq_counter = 1
        all_clone_counter = 0
        collection = []
        for construct in self.constructs:
            clone_counter = 0
            for clone in construct['clones']:
                if only_with_positive_pcr:
                    if clone['pcr_result'] == 'fail' or clone['pcr_result'] == None:
                        continue
                
                collection.append({
                    'clone_identifier': clone['identifier'],
                    'agar_plate_number': clone['agar_plate_number'],
                    'agar_plate_position': clone['agar_plate_position'],
                    'seq_identifier': seq_counter,
                    'seq_result': None,
                })
                seq_counter += 1
                clone_counter += 1
                all_clone_counter += 1
                if max_clones and (clone_counter >= max_clones):
                    break
        
        if all_clone_counter == 0:
            raise NoClonesError('There are no clones in your project.')

        template = pd.DataFrame(collection).set_index('clone_identifier')
        template.to_excel(_filename)

    def read_seq_input(self, filename:str=None):
        """ Reads an Excel file containing a list of constructs.
            
            Args:
                filename (str): Filename for the input. If None, project name + '_seq_results.xlsx' will be used.
        """
        if filename == None:
            _filename = f'{self.project_name}_seq_results.xlsx'
        else:
            _filename = filename

        data = pd.read_excel(_filename).dropna()
        counter = 0
        for _, row in data.iterrows():
            for construct in self.constructs:
                for clone in construct['clones']:
                    if row['clone_identifier'] == clone['identifier']:
                        break
                else:
                    clone = None
                if not clone is None:
                    break
            else:
                raise ValueError(f'Clone {row["clone_identifier"]} could not be found.')

            if row['seq_result'] == 'y':
                clone['seq_result'] = 'success'
                counter += 1
            elif row['seq_result'] == 'n':
                clone['seq_result'] = 'fail'
                counter += 1
        
        print(f'SEQ data for {counter} clones added')

    def as_dataframe(self):
        """ Returns the whole project as a DataFrame.

            Returns:
                dataframe (pandas.DataFrame): All the data. In a frame. 
        """
        collection = []
        for construct in self.constructs:
            if construct['clones']:
                for clone in construct['clones']:
                    new_entry = {'construct': construct['identifier']}
                    new_entry.update(construct['properties'])
                    new_entry.update({
                        'clone': clone['identifier'],
                        'agar_plate_number': clone['agar_plate_number'],
                        'agar_plate_position': clone['agar_plate_position'],
                        'pcr_result': clone['pcr_result'],
                        'seq_result': clone['seq_result'],
                        'storage_plate_number': clone['storage_plate_number'],
                        'storage_plate_position': clone['storage_plate_position'],
                    })
                    collection.append(new_entry)
            else:
                new_entry = {'construct': construct['identifier']}
                new_entry.update(construct['properties'])
                collection.append(new_entry)
        dataframe = pd.DataFrame(collection)

        return dataframe

    def get_validated_clones(self, pcr:bool=True, seq:bool=True, how_many:int=None):
        """ Returns a dataframe containing only clones with positive PCR and/or SEQ result.

            Args:
                pcr (bool): Positive PCR result is required.
                seq (bool): Positive sequencing result is required.
                how_many (int): How many clones per construct. If None, output contains all validated clones

            Returns:
                (pandas.DataFrame): Containing clones with positive PCR and/or SEQ results.
        """
        output = self.as_dataframe()
        if pcr:
            output = output.query('pcr_result == "success"')
        if seq:
            output = output.query('seq_result == "success"')

        if how_many:
            output = output.groupby('construct').sample(how_many)

        return output

    def store_clones(self, pcr:bool=True, seq:bool=True, how_many:int=None):
        """ Sets storage location for (validated) clones. If 'filename' is set, exports a Excel file containing storage locations.

            Args:
                pcr (bool): Positive PCR result is required.
                seq (bool): Positive sequencing result is required.
                how_many (int): How many clones per construct. If None, output contains all validated clones
        """
        plate_counter = 1
        position_counter = 1
        position_mapping = dict(zip(range(1,97), [f'{l}{n}' for n in range(1,13) for l in 'ABCDEFGH' ]))

        for construct in self.constructs:
            if construct['clones']:
                clone_counter = 0
                for clone in construct['clones']:
                    if pcr and (not clone['pcr_result'] or clone['pcr_result'] == 'fail'):
                        continue
                    if seq and (not clone['seq_result']  or clone['seq_result'] == 'fail'):
                        continue
                    clone['storage_plate_number'] = plate_counter
                    clone['storage_plate_position'] = position_mapping[position_counter]
                    if position_counter == 96:
                        position_counter = 1
                        plate_counter += 1
                    else:
                        position_counter += 1
                    
                    clone_counter += 1
                    if how_many and (how_many > 0) and (clone_counter >= how_many):
                        break

    def export_to_excel(self, filename:str=None):
        """ Exports all project data to an Excel file.
        """
        if filename == None:
                _filename = pathlib.Path(f'{self.project_name}.xlsx')
        else:
            _filename = pathlib.Path(filename)

        if _filename.exists():
            raise FileExistsError('File already exists. Please delete the old template or choose a different file name.')

        self.as_dataframe().to_excel(_filename)

    def create_dag(self, include_properties:list=None, include_constructs:list=None, highlight_stored:bool=True):
        """ Visualizes the project as a DAG using graphviz.

        Args:
            include_properties (list): Which properties from the parent constructs to include.
            include_constructs (list): Which constructs to include. If None, all constructs are selected.
            highlight_stored (bool): If true, highlights stored clones and their trail.

        Returns:
            graph (graphviz.Digraph): Resulting graph.
        """
        try:
            from graphviz import Digraph
        except ImportError:
            ModuleNotFoundError('Could not find graphviz module. Please install graphviz and the graphviz python module in order to use this function')
            return
            
        dot = Digraph()

        if include_constructs is None:
            constructs = self.constructs
        else:
            constructs = []
            for construct in self.constructs:
                if construct['identifier'] in include_constructs:
                    constructs.append(construct)

        to_highlight = set()
        if highlight_stored:
            for construct in constructs:
                for clone in construct['clones']:
                    if clone['storage_plate_number']:
                        to_highlight.add(str(clone["identifier"]))
                        to_highlight.add(str(construct["identifier"]))
                        for prop in include_properties:
                            to_highlight.add(str(construct['properties'][prop]))

        def new_node(name, label):
            if name in to_highlight:
                dot.node(name, label, penwidth = '4', color = 'chartreuse')
            else:
                dot.node(name, label, penwidth = '1', color = 'black')

        for construct in constructs:
            n_clones = len(construct['clones'])
            n_pcr = sum([x['pcr_result'] == 'success' for x in construct['clones']])
            n_seq = sum([x['seq_result'] == 'success' for x in construct['clones']])

            cnode_name = str(construct["identifier"])
            cnode_label = f'{str(construct["identifier"])} \n Clones obtained: {n_clones} \n PCR positive: {n_pcr} \n SEQ positive: {n_seq}'

            new_node(cnode_name, cnode_label)

            for prop in include_properties:
                new_node(str(construct['properties'][prop]), str(construct['properties'][prop]))
                dot.edge(str(construct['properties'][prop]), cnode_name)

            for clone in construct['clones']:
                if clone['storage_plate_number']:
                    clonenode_name = str(clone["identifier"])
                    clonenode_label = f'{str(clone["identifier"])} \n Storage: Plate {str(clone["storage_plate_number"])}, Well {str(clone["storage_plate_position"])}'
                    new_node(clonenode_name, clonenode_label)
                    dot.edge(cnode_name, clonenode_name)

        dot.graph_attr['rankdir'] = 'LR'

        return dot


class Construct(TypedDict):
    """Holds data for one construct"""
    identifier: str
    properties: dict
    clones: list


class Clone(TypedDict):
    """Holds data for one clone"""
    identifier: str
    agar_plate_number: int
    agar_plate_position: str
    pcr_result: str
    seq_result: str
    storage_plate_number: int
    storage_plate_position: str
