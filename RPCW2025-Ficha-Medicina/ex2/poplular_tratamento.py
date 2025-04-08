import csv
import re

def format_identifier(name):
    """Formatar identificadores removendo caracteres especiais e substituindo espaços por underscores."""
    name = name.strip().replace(" ", "_")  # <- mantém caixa original
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    return name


def process_treatments(file_path):
    """Ler o CSV e estruturar os dados de tratamentos por doença."""
    disease_treatments = {}
    all_treatments = set()

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            disease = format_identifier(row["Disease"])
            treatments = {
                format_identifier(row["Precaution_1"]),
                format_identifier(row["Precaution_2"]),
                format_identifier(row["Precaution_3"]),
                format_identifier(row["Precaution_4"]),
            }
            disease_treatments[disease] = treatments
            all_treatments.update(treatments)

    return disease_treatments, all_treatments

def generate_ontology(disease_treatments, all_treatments):
    """Gerar as instâncias de tratamentos e associações com as doenças."""
    output = ""

    # Criar instâncias de tratamento
    for treatment in sorted(all_treatments):
        output += f":{treatment} rdf:type :Treatment .\n"

    output += "\n"

    # Gerar associações de :hasTreatment (sem rdf:type da doença)
    for disease, treatments in disease_treatments.items():
        treatment_lines = " ,\n                ".join(f":{t}" for t in sorted(treatments))
        output += f":{disease} \n"
        output += f"         :hasTreatment {treatment_lines} .\n\n"

    return output

# Caminho para o CSV
file_path = 'Disease_Treatment.csv'  # Altere conforme necessário

# Processar dados
disease_treatments, all_treatments = process_treatments(file_path)

# Gerar saída
ontology_output = generate_ontology(disease_treatments, all_treatments)

# Salvar resultado
with open("ontology_only_treatments.ttl", "w", encoding="utf-8") as f:
    f.write(ontology_output)

print("Associações de tratamentos geradas com sucesso!")
