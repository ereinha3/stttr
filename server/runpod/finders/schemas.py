import os
import logging
logger = logging.getLogger(__name__)
from runpod.classes import FoundTemplate, FoundStorage

class SchemaFinder:
    def __init__(self, schema_dir: str):
        self.schema_dir = schema_dir

        # directory structure is the order of the variables in the template
        self.directory_structure = [
            'author', 
            'model', 
            'arch', 
            'gpu_count', 
            'service', 
            'precision'
            ]

        self.schemas = self.fetch_schemas()

    def recurse_subdirectories(self, directory: str):
        file_paths = []
        if not os.path.isdir(directory):
            return file_paths
        for entry in os.listdir(directory):
            if entry == "__pycache__" or entry.startswith('.'):
                continue
            path = os.path.join(directory, entry)

            if entry == '__init__.py':
                file_paths.append(directory)
            elif os.path.isdir(path):
                file_paths.extend(self.recurse_subdirectories(path))
            else:
                raise FileExistsError(f"File __init__.py found in a non-directory {path}")
        return file_paths

    def fetch_schemas(self):
        if not os.path.isdir(self.schema_dir):
            return []
        templates = self.recurse_subdirectories(self.schema_dir)
        templates = [str(template).replace('/', '.') for template in templates]
        
        # Build templates dictionary with graceful auth handling
        templates_dict = {}
        for template in templates:
            template_module = __import__(template, fromlist=['template', 'storage'])
            
            # Template and storage are required
            if not hasattr(template_module, 'template'):
                raise ValueError(f"Template {template} does not have a template attribute")
            if not hasattr(template_module, 'storage'):
                raise ValueError(f"Template {template} does not have a storage attribute")
            
            # Auth is optional - set to None if not available
            
            templates_dict[template] = {
                'template': template_module.template,
                'storage': template_module.storage,
            }
        
        templates = templates_dict
        
        templates_dicts = []
        for template_name, template in templates.items():
            split_name = template_name.split('.')
            split_name.remove(self.schema_dir)
            template_dict = {self.directory_structure[i]: split_name[i] for i in range(len(split_name))}
            template_dict['arch'] = template_dict['arch'].replace('-', ' ')
            
            # Process template and storage (required)
            template['template'] = FoundTemplate(datadict=template_dict, **template['template'].__dict__)
            template['storage'] = FoundStorage(datadict=template_dict, **template['storage'].__dict__)
            
            
            templates_dicts.append(template)

        return templates_dicts
        

if __name__ == "__main__":
    logging.basicConfig(
    level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s \t- %(message)s'
    )
    schema = SchemaFinder(schema_dir="templates")
    schemas = schema.schemas
    logger.info("Available templates:")
    for schema in schemas:
        logger.info('-'*50)
        for key, value in schema.items():
            if key != 'template':
                if key == 'schema' and value is None:
                    logger.info(f"\t{key}: None (not available)")
                else:
                    logger.info(f"\t{key}: {value}")
        logger.info(f"\tTemplate Name: {schema['template'].name}")
        logger.info(f"\tStorage Name: {schema['template'].storage.name}")
        if schema['template'].container_registry_auth is not None:
            logger.info(f"\tAuth Name: {schema['template'].container_registry_auth.name}")
        else:
            logger.info(f"\tAuth: Not available for this schema")
    logger.info('-'*50)
            