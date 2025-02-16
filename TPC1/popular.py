import json

with open('emd.json', 'r', encoding='utf-8') as file:
    dataset = json.load(file)

output = "" 
modalidades = {}
pessoas = {}
clubes = {}

for i, e in enumerate(dataset):
    #Para criar a pessoa só na primeira fez que ele aparece

    if e['email'] not in pessoas:
        pessoas[e['email']] = "P" + str(len(pessoas))
        output += f"""
        ###  http://rpcw.di.uminho.pt/2025/EMD#{pessoas[e['email']]}
            :{pessoas[e['email']]} rdf:type owl:NamedIndividual ,
                         :Pessoa ;
                :email "{e['email']}" ;
                :género "{e['género']}" ;
                :idade {e['idade']} ;
                :morada "{e['morada']}" ;
                :nome "{e['nome']['primeiro']} {e['nome']['último']}" .
        """
    idPessoa = pessoas[e['email']]

    #Para criar o clube só na primeira fez que ele aparece
    if e['clube'] not in clubes:
        clubes[e['clube']] = "C" + str(len(clubes))
        output += f"""
        ###  http://rpcw.di.uminho.pt/2025/EMD#{clubes[e['clube']]}
        :{clubes[e['clube']]} rdf:type owl:NamedIndividual ,
                     :Clube ;
            :temAtleta :{idPessoa} ;
            :nome "{e['clube']}".
        """
    idClube = clubes[e['clube']]
    
    # se a modalidade não existir ela é criada
    if e['modalidade'] not in modalidades:
        modalidades[e['modalidade']] = "M" + str(len(modalidades))
        output += f"""
        ###  http://rpcw.di.uminho.pt/2025/EMD#{modalidades[e['modalidade']] }
        :{modalidades[e['modalidade']] } rdf:type owl:NamedIndividual ,
                     :Modalidade ;
            :temExame :E{i};
            :éPraticadaEm :{idClube} ;
            :éPraticadaPor :{idPessoa} ;
            :nome "{e['modalidade']}" .
        """
    # Para o caso em que a pessoa possa ter várias modalidades
    else: 
        output += f"""
            :{modalidades[e['modalidade']] } :temExame :E{i};
                                             :éPraticadaEm :{idClube} ;
                                             :éPraticadaPor :{idPessoa} .
        """
        
    output += f"""
    ###  http://rpcw.di.uminho.pt/2025/EMD#E{i}
    :E{i} rdf:type owl:NamedIndividual ,
                 :Exame ;
        :éRealizadoPor :{idPessoa} ;
        :dataEMD "{e['dataEMD']}" ;
        :resultado "{str(e['resultado']).lower()}"^^xsd:boolean .   
         
    """
    
    print(output)

      
   