import json
import re

def format_identifier(name):
    """Formata identificadores (ex: sintomas) em estilo RDF válido."""
    name = name.strip().replace(" ", "_").lower()
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    return name

def generate_patients_ontology(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        patients = json.load(f)

    output = ""
    for i, patient in enumerate(patients, start=1):
        patient_id = f"Patient{i}"
        name = patient.get("nome", "Desconhecido").replace('"', "'")  # evita conflito com aspas duplas
        sintomas = patient.get("sintomas", [])

        # Formatar sintomas
        sintomas_rdf = " ,\n                   ".join(f":{format_identifier(s)}" for s in sintomas)

        # Montar bloco RDF do paciente
        output += f":{patient_id} rdf:type owl:NamedIndividual ,\n"
        output += f"           :Patient ;\n"
        if sintomas_rdf:
            output += f"           :exhibitsSymptom {sintomas_rdf} ;\n"
        output += f"           :name \"{name}\" .\n\n"

    return output

# Caminho para o arquivo JSON
json_path = "doentes.json"  # Altere conforme necessário

# Gerar ontologia dos pacientes
ontology_output = generate_patients_ontology(json_path)

# Salvar em arquivo
with open("ontology_patients.ttl", "w", encoding="utf-8") as f:
    f.write(ontology_output)

print("Instâncias dos doentes geradas com sucesso!")
