from antlr4 import CommonTokenStream, FileStream, ParseTreeWalker
from besser.BUML.metamodel.structural import DomainModel
from .PlantUMLLexer import PlantUMLLexer
from .PlantUMLParser import PlantUMLParser
from .plantUML_buml_listener import BUMLGenerationListener

def plantuml_to_buml(plantUML_model_path:str, buml_model_file_name:str = "buml_model"):
    """Transforms a PlantUML model into a B-UML model.

    Args:
        plantUML_model_path (str): The path to the file containing the PlantUML code.
        buml_model_file_name (str, optional): the name of the file produced with the base 
                code to build the B-UML model.

    Returns:
        BUML_model (DomainModel): the B-UML model object.
    """
    lexer = PlantUMLLexer(FileStream(plantUML_model_path))
    parser = PlantUMLParser(CommonTokenStream(lexer))
    parse_tree = parser.domainModel()
    listen = BUMLGenerationListener()
    walker = ParseTreeWalker()
    walker.walk(listen, parse_tree)
    domain_model: DomainModel = listen.get_buml_model()
    return domain_model
