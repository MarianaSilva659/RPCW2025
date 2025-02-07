import json
from rdflib import Graph, URIRef, Literal, XSD, RDF

BASE_URI = "http://www.semanticweb.org/mariana/ontologies/2025/untitled-ontology-10"

graph = Graph()
graph.parse("dominio.ttl", format="ttl")

with open('emd.json', 'r', encoding='utf-8') as file:
    dataset = json.load(file)
    
#definir os uri para os atributos

temExame = URIRef(BASE_URI + "temExame")
frequentaModalidade = URIRef(BASE_URI + "frequentaModalidade")

_id = URIRef(BASE_URI + "_id")
primeiroNome = URIRef(BASE_URI + "primeiroNome")
segundoNome = URIRef(BASE_URI + "segundoNome")
idade = URIRef(BASE_URI + "idade")
género = URIRef(BASE_URI + "género")
morada = URIRef(BASE_URI + "morada")
email = URIRef(BASE_URI + "email")
federado = URIRef(BASE_URI + "federado")
resultado = URIRef(BASE_URI + "resultado")
dataEMD = URIRef(BASE_URI + "dataEMD")
nomeModalidade = URIRef(BASE_URI + "nomeModalidade")
clube = URIRef(BASE_URI + "clube")

for entry in dataset:
    id_Pessoa = str(entry["_id"])
    dataEMD_Exame = entry["dataEMD"]
    primeiroNome_Pessoa = entry["nome"]["primeiro"]
    segundoNome_Pessoa = entry["nome"]["último"]
    idade_Pessoa = entry["idade"]
    género_Pessoa = entry["género"]
    morada_Pessoa = entry["morada"]
    modalidade  = entry["modalidade"]
    clube_Modaliade = entry["clube"]
    email_Pessoa = entry["email"]
    federado_Pessoa = entry["federado"]
    resultado_Exame = entry["resultado"]
    
    uri_modalidade = URIRef(BASE_URI + "Modalidade/" + modalidade)
    uri_exame = URIRef(BASE_URI + "Exame/" + id_Pessoa)
    uri_Pessoa = URIRef(BASE_URI + "Pessoa/" + id_Pessoa)
    
    #Atributos Pessoa
    graph.add((uri_Pessoa, RDF.type, URIRef(BASE_URI + "Pessoa")))
    graph.add((uri_Pessoa, _id, Literal(id_Pessoa, datatype=XSD.string)))
    graph.add((uri_Pessoa, primeiroNome, Literal(primeiroNome_Pessoa, datatype=XSD.string)))
    graph.add((uri_Pessoa, segundoNome, Literal(segundoNome_Pessoa, datatype=XSD.string)))
    graph.add((uri_Pessoa, idade, Literal(idade_Pessoa, datatype=XSD.int)))
    graph.add((uri_Pessoa, género, Literal(género_Pessoa, datatype=XSD.string)))
    graph.add((uri_Pessoa, morada, Literal(morada_Pessoa, datatype=XSD.string)))
    graph.add((uri_Pessoa, email, Literal(email_Pessoa, datatype=XSD.string)))
    graph.add((uri_Pessoa, federado, Literal(federado_Pessoa, datatype=XSD.boolean)))
    
    # Relações entre Pessoa e Modalidade/Exame
    graph.add((uri_Pessoa, frequentaModalidade, uri_modalidade))
    graph.add((uri_Pessoa, temExame, uri_exame))
    
    # Atributos Exame
    graph.add((uri_exame, RDF.type, URIRef(BASE_URI + "Exame")))
    graph.add((uri_exame, _id, Literal(id_Pessoa, datatype=XSD.string)))
    graph.add((uri_exame, dataEMD, Literal(dataEMD_Exame, datatype=XSD.string)))
    graph.add((uri_exame, resultado, Literal(resultado_Exame, datatype=XSD.boolean)))

    #Atributos Modalidade
    graph.add((uri_modalidade, RDF.type, URIRef(BASE_URI + "Modalidade")))
    graph.add((uri_modalidade, nomeModalidade, Literal(modalidade, datatype=XSD.string)))
    graph.add((uri_modalidade, clube, Literal(clube_Modaliade, datatype=XSD.string)))

graph.serialize(destination="dominioPopulado.ttl", format="turtle")