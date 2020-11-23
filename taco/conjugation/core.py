import pathlib
import pandas as pd
import numpy as np
from typing import TypedDict

from .. import TacoProject
from .. utils import NoClonesError

class ConjugationProject():
    """Holds project data"""
    def __init__(self, taco_project:TacoProject):
        self._project_name = taco_project.project_name + '_conjugation'
        self.tp = taco_project
        self.constructs = list()

    @property
    def project_name(self) -> str:
        """Contains the name of the project."""
        return self._project_name

    def generate_conjugation_template(self, filename:str=None, number_of_plates:int=1, pcr_positive:bool=True, seq_positive:bool=False):
        """ Generates an Excel file to be used as template for a conjugation run. 
        The function selects at least one positive clone per construct and fills up to run capacity.

        Args:
            filename (str): Filename for the exported template. If None, project name + '_template.xlsx' will be used.
            number_of_plates (int): How many conjugation plates (96 well) should be prepared.
            pcr_positive (bool): Only take clones with a positive colony PCR result.
            seq_positive (bool): Only take clones with a positive sequencing result.
        """
        if filename == None:
            _filename = pathlib.Path(f'{self.project_name}_template.xlsx')
        else:
            _filename = pathlib.Path(filename)

        plate = np.concatenate([np.repeat(i+1, 96) for i in range(number_of_plates)])
        pos = np.concatenate([np.array([f'{l}{n}' for n in range(1,13) for l in 'ABCDEFGH']) for i in range(number_of_plates)])
        inputdata = self.tp.get_validated_clones(pcr=pcr_positive, seq=seq_positive)

        n = 1
        constructs = []
        clones = []
        while len(constructs) < number_of_plates*96:
            subset = inputdata.groupby('construct').nth(n)
            if len(subset) == 0:
                n = 1
            else:
                constructs += list(subset.index)
                clones += list(subset.loc[:, 'clone'])
                n += 1

        template = pd.DataFrame(
            [constructs[0:number_of_plates*96],
            clones[0:number_of_plates*96],
            plate, pos, np.repeat(np.nan, number_of_plates*96)],
        ).T
        template.columns = pd.Index(['construct', 'clone', 'conjugation_plate', 'conjugation_position', 'number_of_clones'])
        template.to_excel(_filename)

    def read_conjugation_result(self, filename:str=None):
        """ Reads an Excel file containing a list of conjugated constructs.
            
            Args:
                filename (str): Filename for the input. If None, project name + '_conjugation_results.xlsx' will be used.
        """
        if filename == None:
            _filename = f'{self.project_name}_conjugation_results.xlsx'
        else:
            _filename = filename

        data = pd.read_excel(_filename)

        clone_counter = 0
        for _, row in data.iterrows():
            clones = []
            for i in range(1, row['number_of_clones'] + 1):
                new_clone: Clone = {
                    'identifier': f"{row['construct']}_Conj_{i}",
                    'origin': row['clone'],
                    'conjugation_plate_number': row['conjugation_plate_number'],
                    'conjugation_position': row['conjugation_position'],
                    'growth_result': None,
                    'storage_plate_number': None,
                    'storage_plate_position': None,
                }
                clones.append(new_clone)
                clone_counter += 1
            try:
                construct = next(x for x in self.constructs if x['identifier'] == row['construct'])
                construct['clones'] += clones
            except StopIteration:
                new_construct: Construct = {
                    'identifier': row['construct'],
                    'clones': list(),
                }
                new_construct['clones'] += clones
                self.constructs.append(new_construct)
            
        print(f'{clone_counter} conjugation clones were added to the project.')

    def generate_growth_template(self, filename:str=None, max_clones:int=None, use_mtp=False):
        """ Generates an Excel file to be used as a template for a grwoth experiment.
            
            Args:
                max_clones (int): Maximum number of clones to test. If None, all clones of each construct are choosen. 
                filename (str): Filename for the input template. If None, project name + '_growth.xlsx' will be used.
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

        growth_counter = 1
        growth_plate_counter = 1
        growth_position_counter = 1
        growth_position_mapping = dict(zip(range(1,97), [f'{l}{n}' for l in 'ABCDEFGH' for n in range(1,13)]))
        all_clone_counter = 0

        collection = []
        for construct in self.constructs:
            clone_counter = 0
            for clone in construct['clones']:
                new_entry = {
                    'construct_identifier': construct['identifier'],
                    'clone_identifier': clone['identifier'],
                    'conjugation_plate_number': clone['conjugation_plate_number'],
                    'conjugation_position': clone['conjugation_position'],
                    'growth_exp_identifier': growth_counter,
                }
                if use_mtp:
                    new_entry.update({
                        'growth_plate': growth_plate_counter,
                        'growth_plate_position': growth_position_mapping[growth_position_counter],
                    })
                new_entry.update({'growth_result': None})
                collection.append(new_entry)
                growth_counter += 1
                clone_counter += 1
                all_clone_counter += 1

                if growth_position_counter == 96:
                    growth_position_counter = 1
                    growth_plate_counter += 1
                else:
                    growth_position_counter += 1

                if max_clones and (clone_counter >= max_clones):
                    break
        
        if all_clone_counter == 0:
            raise NoClonesError('There are no clones in your project.')

        template = pd.DataFrame(collection)
        template.to_excel(_filename)

    def read_growth_input(self, filename:str=None):
        """ Reads an Excel file containing results from an growth experiment.
            
            Args:
                filename (str): Filename for the input. If None, project name + '_growth_results.xlsx' will be used.

        """
        if filename == None:
            _filename = f'{self.project_name}_growth_results.xlsx'
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

            if row['growth_result'] == 'y' or row['growth_result'] == True:
                clone['growth_result'] = 'success'
                counter += 1
            elif row['growth_result'] == 'n' or row['growth_result'] == False:
                clone['growth_result'] = 'fail'
                counter += 1

        print(f'Growth data for {counter} clones added')

    def as_dataframe(self):
        """ Returns the conjugation project as a DataFrame.

            Returns:
                dataframe (pandas.DataFrame): All the data. In a frame. 
        """
        collection = []
        for construct in self.constructs:
            if construct['clones']:
                for clone in construct['clones']:
                    new_entry = {'construct': construct['identifier']}
                    new_entry.update({
                        'clone': clone['identifier'],
                        'origin': clone['origin'],
                        'conjugation_plate_number': clone['conjugation_plate_number'],
                        'conjugation_position': clone['conjugation_position'],
                        'growth_result': clone['growth_result'],
                        'storage_plate_number': clone['storage_plate_number'],
                        'storage_plate_position': clone['storage_plate_position'],
                    })
                    collection.append(new_entry)
            else:
                new_entry = {'construct': construct['identifier']}
                collection.append(new_entry)
        dataframe = pd.DataFrame(collection)

        return dataframe

    def get_validated_clones(self, how_many:int=None):
        """ Returns a dataframe containing only clones with positive growth result.

            Args:
                how_many (int): How many clones per construct. If None, output contains all validated clones

            Returns:
                (pandas.DataFrame): Containing clones with positive growth result.
        """
        output = self.as_dataframe().query('growth_result == "success"')

        if how_many:
            output = output.groupby('construct').sample(how_many)

        return output
    
    def store_clones(self, growth:bool=True, how_many:int=None):
        """ Sets storage location for (validated) clones. If 'filename' is set, exports a Excel file containing storage locations.

            Args:
                growth (bool): Positive growth result is required.
                how_many (int): How many clones per construct. If None, output contains all validated clones
        """
        plate_counter = 1
        position_counter = 1
        position_mapping = dict(zip(range(1,97), [f'{l}{n}' for n in range(1,13) for l in 'ABCDEFGH' ]))

        for construct in self.constructs:
            if construct['clones']:
                clone_counter = 0
                for clone in construct['clones']:
                    if growth and (not clone['growth_result'] or clone['growth_result'] == 'fail'):
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
                        to_highlight.add(f'Conjugation_{str(construct["identifier"])}')
                        parent = next(x for x in self.tp.constructs if x['identifier'] == construct['identifier'])
                        for prop in include_properties:
                            to_highlight.add(str(parent['properties'][prop]))

        def new_node(name, label):
            if name in to_highlight:
                dot.node(name, label, penwidth = '4', color = 'chartreuse')
            else:
                dot.node(name, label, penwidth = '1', color = 'black')

        for construct in constructs:
            n_clones = len(construct['clones'])
            n_growth = sum([x['growth_result'] == 'success' for x in construct['clones']])

            cnode_name = str(construct["identifier"])
            new_node(cnode_name, cnode_name)

            conjugation_name = f'Conjugation_{str(construct["identifier"])}'
            conjugation_label = f'Conjugation \n {str(construct["identifier"])} \n Clones: {n_clones}, Growth positive: {n_growth}'
            new_node(conjugation_name, conjugation_label)
            dot.edge(cnode_name, conjugation_name)

            parent = next(x for x in self.tp.constructs if x['identifier'] == construct['identifier'])
            for prop in include_properties:
                new_node(str(parent['properties'][prop]), str(parent['properties'][prop]))
                dot.edge(str(parent['properties'][prop]), cnode_name)

            for clone in construct['clones']:
                if clone['storage_plate_number']:
                    clonenode_name = str(clone["identifier"])
                    clonenode_label = f'{str(clone["identifier"])} \n Storage: Plate {str(clone["storage_plate_number"])}, Well {str(clone["storage_plate_position"])}'
                    new_node(clonenode_name, clonenode_label)
                    dot.edge(conjugation_name, clonenode_name)

        dot.graph_attr['rankdir'] = 'LR'

        return dot
    
class Construct(TypedDict):
    """Holds data for one construct"""
    identifier: str
    clones: list

class Clone(TypedDict):
    """Holds data for one clone"""
    identifier: str
    origin: str
    conjugation_plate_number: int
    conjugation_position: str
    storage_plate_number: int
    storage_plate_position: str
