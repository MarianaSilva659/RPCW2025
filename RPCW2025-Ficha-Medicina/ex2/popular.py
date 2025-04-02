import json
import re
import csv

def format_identifier(name):
    """Formatar identificadores removendo caracteres especiais e substituindo espaços por underscores."""
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    return name

def process_csv(file_path):
    """Ler o CSV e estruturar os dados em um dicionário."""
    diseases = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Captura os nomes das colunas
        
        for row in reader:
            disease_name = format_identifier(row[0])
            symptoms = [format_identifier(symptom) for symptom in row[1:] if symptom]
            
            if disease_name not in diseases:
                diseases[disease_name] = set()
            
            diseases[disease_name].update(symptoms)
    
    return diseases

def generate_ontology(diseases):
    """Gerar a ontologia OWL baseada nos dados das doenças e sintomas."""
    output = ""
    
    for disease, symptoms in diseases.items():
        output += f"""
:{disease} rdf:type owl:NamedIndividual , :Disease ;
    :hasSymptom {', '.join(f':{symptom}' for symptom in symptoms)} .
        """
        
        for symptom in symptoms:
            output += f"""
            :{symptom} a :Symptom .
            """
    
    return output

file_path = 'Disease_Syntoms.csv'  

diseases_data = process_csv(file_path)
ontology_output = generate_ontology(diseases_data)

# Salvar o resultado em um arquivo
with open("ontology_output.txt", "w", encoding="utf-8") as f:
    f.write(ontology_output)

print("Ontologia gerada com sucesso!")
