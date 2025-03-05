from flask import Flask, render_template, request, session, redirect, url_for
from flask_cors import CORS
import random
import requests
from tabulate import tabulate

app = Flask(__name__)
app.secret_key = 'Historia de Portugal'
CORS(app)

# Função para buscar dados do GraphDB
def query_graphdb(endpoint_url, sparql_query):
    headers = {
        'Accept': 'application/json',  
    }
    
    response = requests.get(endpoint_url, params={'query': sparql_query}, headers=headers)
    
    if response.status_code == 200:
        return response.json()  
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

# Consulta SPARQL ao GraphDB
endpoint = "http://localhost:7200/repositories/HistoriaPT"
sparql_query = """
prefix : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?name ?data WHERE {
  ?rei a ex:Rei .
  ?rei :nome ?name .
  ?rei :nascimento ?data .
}
"""

# Obter dados do GraphDB
result = query_graphdb(endpoint, sparql_query)

listaReis = []
for r in result['results']['bindings']:
    t = {
        "name": r['name']['value'].split('#')[-1],
        "dataNasc": r['data']['value'].split('#')[-1]
    }
    listaReis.append(t)


#A dinastia em que cada rei reinou.
sparql_query2 = """
prefix : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?name ?nomeDinastia WHERE {
  ?rei a ex:Rei .
  ?rei :nome ?name .
  ?reinado :temMonarca ?rei .
  ?reinado :dinastia ?dinastia .
  ?dinastia :nome ?nomeDinastia
}
"""

result2 = query_graphdb(endpoint, sparql_query2)
listaReis_Dinastia = []
for r in result2['results']['bindings']:
    t = {
        "name": r['name']['value'],
        "nomeDinastia": r['nomeDinastia']['value']
    }
    listaReis_Dinastia.append(t)

sparql_query3 = """
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT  ?nome (COUNT(?militante) AS ?total) WHERE {
  ?p a ex:Partido .
  ?p :temMilitante ?militante .
  ?p :nome ?nome
}
GROUP BY ?nome
"""
#Qual a distribuição dos militantes por cada partido politico?
result3 = query_graphdb(endpoint, sparql_query3)
lista_num_militante = []
for r in result3['results']['bindings']:
    t = {
        "name": r['nome']['value'],
        "numMilitantes": r['total']['value']
    }
    lista_num_militante.append(t)


dict_perguntas = dict()

dict_perguntas[0] = ("listaReis_Dinastia", listaReis_Dinastia)
dict_perguntas[1] = ("listaReis", listaReis)
dict_perguntas[2] = ("lista_num_militante", lista_num_militante)


reis = random.sample(dict_perguntas[0][1], 4)
print("reis", reis)

@app.route('/')
def home():
    session['score'] = 0
    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['POST'])
def quiz():
        # Processar a resposta do usuário
        user_answer = request.form.get('answer')
        answer_correct = request.form.get('answerCorrect')

        correct = answer_correct == user_answer
        session['score'] = session.get('score', 0) + (1 if correct else 0)
        
        return render_template('result.html', correct=correct, correct_answer=answer_correct, score=session['score'])

        
@app.route('/quiz', methods=['GET'])
def quiz2():
    tipo_pergunta = random.randint(0, 1)
    opção_pergunta = random.randint(0, 2)
    nome, lista = dict_perguntas[opção_pergunta]
    print("Lista escolhida:", nome)
    # Escolha múltipla
    if tipo_pergunta == 0:
        if nome == "listaReis":
            reis = random.sample(lista, 4)
           # print("reis", reis)
            rei_selecionado = random.choice(reis)
            question = {
                "question": f"Quando nasceu o rei {rei_selecionado['name']}?",
                "options": [rei['dataNasc'] for rei in reis],  # Opções aleatórias de resposta
                "answer": rei_selecionado['dataNasc'],
                "tipo" : 0
            }
        elif nome == "listaReis_Dinastia":
            reis = random.sample(lista, 4)
            rei_selecionado = random.choice(reis)
            question = {
                "question": f"O rei {rei_selecionado['name']} pertence a qual dinastia?",
                "options": [rei['nomeDinastia'] for rei in reis], 
                "answer": rei_selecionado['nomeDinastia'],
                "tipo" : 0
            }
        elif nome == "lista_num_militante":
            partidos = random.sample(lista, 4)
            partido_selecionado = random.choice(partidos)
            question = {
                "question": f"Quantos militantes tem o partido {partido_selecionado['name']}?",
                "options": [partido['numMilitantes'] for partido in partidos], 
                "answer": partido_selecionado['numMilitantes'],
                "tipo" : 0
            }
    else:
        seleção = random.sample(lista, 4)
        chave_selecionado = random.choice(seleção)
        pergunta_selecionada = random.choice(seleção)
        if nome == "listaReis_Dinastia":
            #V/F
            print("reis", seleção)
            resposta_correta = "Verdadeiro" if chave_selecionado['nomeDinastia'] == pergunta_selecionada['nomeDinastia'] else "Falso"
            print("resposta", resposta_correta)
            question = {
                "question": f"O rei {chave_selecionado['name']} reinou na dinastia {pergunta_selecionada['nomeDinastia']}?",
                "options": ["Verdadeiro", "False"],  # Opções aleatórias de resposta
                "answer": resposta_correta,
                "tipo": 1
            }
        elif nome == "lista_num_militante":
           # print("partido", seleção)
            resposta_correta = "Verdadeiro" if chave_selecionado['numMilitantes'] == pergunta_selecionada['numMilitantes'] else "Falso"
            print("resposta", resposta_correta)
            question = {
                "question": f"O partido {chave_selecionado['name']} tem {pergunta_selecionada['numMilitantes']} militantes?",
                "options": ["Verdadeiro", "False"],  
                "answer": resposta_correta,
                "tipo": 1
            }
        else:
           # print("reis", seleção)
            resposta_correta = "Verdadeiro" if chave_selecionado['dataNasc'] == pergunta_selecionada['dataNasc'] else "Falso"
            question = {
                "question": f"O rei {chave_selecionado['name']} nasceu em {pergunta_selecionada['dataNasc']}?",
                "options": ["Verdadeiro", "False"],  
                "answer": resposta_correta,
                "tipo": 1
            }
            
    return render_template('quiz.html', question=question)

@app.route('/score')
def score():
    return render_template('score.html', score=session.get('score', 0))

if __name__ == '__main__':
    app.run(debug=True)
