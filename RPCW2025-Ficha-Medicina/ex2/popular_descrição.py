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
    descriptions = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Captura os nomes das colunas
        
        for row in reader:
            disease_name = format_identifier(row[0])
            description = row[1].strip() if len(row) > 1 else ""
            
            diseases[disease_name] = set()
            descriptions[disease_name] = description
    
    return diseases, descriptions

def generate_ontology(diseases, descriptions):
    """Gerar a ontologia OWL baseada nos dados das doenças e descrições."""
    output = ""
    
    for disease, symptoms in diseases.items():
        description_text = f' :descrição "{descriptions[disease]}" .' if disease in descriptions else ""
        output += f"""

        :{disease} {description_text}
        """
    
    return output

# Caminho para o arquivo CSV
file_path = 'Disease_Description.csv'  # Altere para o caminho correto do seu arquivo

diseases_data, disease_descriptions = process_csv(file_path)
ontology_output = generate_ontology(diseases_data, disease_descriptions)

# Salvar o resultado em um arquivo
with open("ontology_output_descriçãp.txt", "w", encoding="utf-8") as f:
    f.write(ontology_output)

print("Ontologia gerada com sucesso!")
