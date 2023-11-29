from BUML.metamodel.structural import DomainModel, Class, Property, PrimitiveDataType, \
     BinaryAssociation, Multiplicity, Constraint, Generalization, GeneralizationSet
from textx import metamodel_from_file
import os

def __association_name_helper(from_class_name, to_class_name, from_bool, to_bool, from_max, to_max):
    if any(from_bool):
        if from_max == 1: 
            return from_class_name.lower()
        else:
            return from_class_name.lower() + "s"
    elif any(to_bool):
        if to_max == 1: 
            return to_class_name.lower()
        else:
            return to_class_name.lower() + "s" 
    else:
        # This shouldn't be possible actually
        return "variable"

def plantuml_to_buml(model_path:str) -> DomainModel:
    """
    Converts a PlantUML model to a model conforms to B-UML.

    Args:
        model_path (str): The path to the PlantUML model file.

    Returns:
        DomainModel: The resulting model conforms to B-UML.
    """
    
    grammar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plantuml.tx')
    plantUML_mm = metamodel_from_file(grammar_path)
    textx_model = plantUML_mm.model_from_file(model_path)
    model: DomainModel = DomainModel(name="StructuralModel")
    inheritanceGroup: int = 0

    # Class transformation
    for element in textx_model.elements:
        element_type: str = element.__class__.__name__
        if element_type == "Class":
            new_class: Class = Class(name=element.name, is_abstract=element.isAbstract, attributes=set())
            # Attributes and operations definition
            attrs: set[Property] = set()
            opers: set[Property] = set()
            for content in element.classContents:
                # Attributes
                if content.__class__.__name__ == "Attribute":
                    attrs.add(Property(name=content.name, visibility="public", owner=new_class, 
                                       property_type=PrimitiveDataType(name=content.type)))
                # Operations
                # if content.__class__.__name__ == "Method":
            new_class.attributes = attrs
            # Add new class to the model
            model.types.add(new_class)
        if element_type == "SkinParam":
            inheritanceGroup = element.group
    
    # Association definition
    for element in textx_model.elements:
        element_type: str = element.__class__.__name__
        if element_type == "Bidirectional" or element_type == "Unidirectional" or \
            element_type == "Aggregation" or element_type == "Composition":
            # reference from
            class_from: Class = model.get_class_by_name(element.fromClass.name)
            min_from = 1
            max_from = 1
            if element.fromCar is not None: 
                if element.fromCar.min == "*" and element.fromCar.max is None:
                    min_from = 0
                elif element.fromCar.min is not None:
                    min_from = element.fromCar.min                
                max_from = element.fromCar.min if element.fromCar.max is None else element.fromCar.max
            navigable_from: bool = True
            composition_from: bool = False
            aggregation_from: bool = False
            # reference to
            class_to: Class = model.get_class_by_name(element.toClass.name)
            min_to = 1
            max_to = 1
            if element.toCar is not None: 
                if element.toCar.min == "*" and element.toCar.max is None:
                    min_to = 0
                elif element.toCar.min is not None:
                    min_to = element.toCar.min                
                max_to = element.toCar.min if element.toCar.max is None else element.toCar.max
            navigable_to: bool = True
            composition_to: bool = False
            aggregation_to: bool = False
            ends: set[Property] = set()
            if element.__class__.__name__ == "Unidirectional":
                navigable_from = element.fromNav
                navigable_to = element.toNav
            if element.__class__.__name__ == "Aggregation":
                aggregation_from = element.fromAgg
                aggregation_to = element.toAgg            
            if element.__class__.__name__ == "Composition":
                composition_from = element.fromComp
                composition_to = element.toComp
            if element.name is None or element.name == "":
                if element.__class__.__name__ == "Bidirectional":
                    element.name = class_from.name + class_to.name
                else:
                    element.name = __association_name_helper(class_from.name, class_to.name, [navigable_from, aggregation_from, composition_from], [navigable_to, aggregation_to, composition_to], max_from, max_to)
            ends.add(Property(name=element.name, visibility="public", owner=class_from, property_type=class_from, 
                              multiplicity=Multiplicity(min_multiplicity=min_from,max_multiplicity=max_from), 
                              is_composite=composition_from, is_navigable=navigable_from, is_aggregation=aggregation_from))
            ends.add(Property(name=element.name, visibility="public", owner=class_to, property_type=class_to, 
                              multiplicity=Multiplicity(min_multiplicity=min_to, max_multiplicity=max_to), 
                              is_composite=composition_to, is_navigable=navigable_to, is_aggregation=aggregation_to))
            new_association: BinaryAssociation = BinaryAssociation(name=element.name, ends=ends)
            model.associations.add(new_association)
        
        # Generalization definition
        if element_type == "Inheritance":
            if element.fromInh == True:
                generalClass: Class = model.get_class_by_name(element.fromClass.name)
                specificClass: Class = model.get_class_by_name(element.toClass.name)
            elif element.toInh == True:
                generalClass: Class = model.get_class_by_name(element.toClass.name)
                specificClass: Class = model.get_class_by_name(element.fromClass.name)
            if element.fromInh != element.toInh:               
                new_generalization: Generalization = Generalization(general=generalClass, specific=specificClass)
                model.generalizations.add(new_generalization)
    
    # Generalization group definition
    if inheritanceGroup > 1:
        gen_classes_list = []
        gen_classes_set = set()
        for generalization in model.generalizations:
            gen_classes_list.append(generalization.general)
            gen_classes_set.add(generalization.general)

        for general in gen_classes_set:
            if gen_classes_list.count(general) >= inheritanceGroup:
                generalizations: set = []
                for generalization in model.generalizations:
                    if general == generalization.general:
                        generalizations.append(generalization)
                new_generalizationSet: GeneralizationSet = GeneralizationSet(name="gen-set-" + general.name, generalizations=generalizations, 
                                                                             is_disjoint=True, is_complete=True)

    # Constraint definition
    for element in textx_model.oclConstraints:
        context: Class = model.get_class_by_name(element.context.name)
        new_constraint: Constraint = Constraint(name=element.name, context=context, expression=element.expression, language="OCL")
        model.constraints.add(new_constraint)
    return model



