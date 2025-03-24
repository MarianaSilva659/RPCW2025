import json
import re

def format_identifier(name):
    name = name.replace(" ", "_")  
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    return name

with open('movies.json', 'r', encoding='utf-8') as file:
    dataset = json.load(file)

output = "" 
pessoas = {}
genero = []
paises = []
linguas = []
lingua_movie = ""
pais_movie = ""

for i, filme in enumerate(dataset["movies"]):
    for pessoa in filme["pessoasRelacionadas"]:
        if pessoa["name"] not in pessoas:
            nome = format_identifier(pessoa["name"])
            output += f"""
        ###  http://www.semanticweb.org/mariana/ontologies/cinema#{nome}
        :{nome} rdf:type owl:NamedIndividual ,
                          :Pessoa .
        """

    for g in filme["género"]:
            genero_str = " , ".join(f":{g}" for g in filme["género"]) + " ;"

            if g not in genero:
                genero.append(g)
                output += f"""
                ###  http://www.semanticweb.org/mariana/ontologies/cinema#{g}
                :{g} rdf:type owl:NamedIndividual ,
                        :Género .
                """
    
    if filme["PaisOrigem"] not in paises:
        paises.append(filme["PaisOrigem"])
        pais_movie = filme["PaisOrigem"]
        output += f"""
        ###  http://www.semanticweb.org/mariana/ontologies/cinema#{filme["PaisOrigem"]}
        :{filme["PaisOrigem"]} rdf:type owl:NamedIndividual ,
                   :País .
        """ 
    elif filme["linguaOriginal"] not in linguas and filme["linguaOriginal"] != None:
        linguas.append(filme["linguaOriginal"])
        lingua_movie = filme["linguaOriginal"]
        output += f"""
        ###  http://www.semanticweb.org/mariana/ontologies/cinema#{filme["linguaOriginal"]}
        :{filme["linguaOriginal"]} rdf:type owl:NamedIndividual ,
                 :Língua .
        """ 
    else:
        nome = format_identifier(filme["tituloOriginal"])
        
        output += f"""
    ###  http://www.semanticweb.org/mariana/ontologies/cinema#{nome}
    : rdf:{nome}type owl:NamedIndividual ,
                       :Filme ;
              :temArgumento :Argumento{nome} ;
              :temGénero {genero_str}
              :temLíngua :{lingua_movie};
              :temPaisOrigem :{pais_movie} ;
              :data "{filme["ano"]}" ;
              :duração "{filme["duração"]}"^^xsd:int .
    """
    
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(output)
      
   