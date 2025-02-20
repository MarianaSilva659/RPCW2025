# TPC 2

### Tarefa
 Finalizar as queries pedidas em SPARQL.


#### Quais classes existem


```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# Quais classes existem
SELECT ?classe WHERE {
  ?classe a owl:Class .
}
```


#### Que propriedades tem a classe "Rei"? 

```PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
# Ir buscar as propriedades do rei 
SELECT distinct ?prop WHERE {
  ?s a :Rei .
  ?s ?prop ?o .
} order by ?prop
```
#### Quantos reis aparecem na ontologia?

```
prefix : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT (COUNT(?rei) AS ?total)
WHERE {
  ?rei a ex:Rei .
}
```

###### Resultado : 32

#### Calcula uma tabela com o seu nome, data de nascimento e cognome.
```
prefix : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?rei ?name ?data ?cgn WHERE {
  ?rei a ex:Rei .
  ?rei :nome ?name .
  ?rei :nascimento ?data .
  ?rei :cognomes ?cgn
}
```
#### Acrescenta à tabela anterior a dinastia em que cada rei reinou.

```
prefix : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?rei ?name ?data ?cgn ?nomeDinastia WHERE {
  ?rei a ex:Rei .
  ?rei :nome ?name .
  ?rei :nascimento ?data .
  ?rei :cognomes ?cgn .
  ?reinado :temMonarca ?rei .
  ?reinado :dinastia ?dinastia .
  ?dinastia :nome ?nomeDinastia
  
}
```
#### Qual a distribuição de reis pelas 4 dinastias?

```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?nomeDinastia (COUNT(?rei) AS ?totalReis)
WHERE {
  ?rei a ex:Rei .
  ?reinado :temMonarca ?rei .
  ?reinado :dinastia ?dinastia .
  ?dinastia :nome ?nomeDinastia .
}
GROUP BY ?nomeDinastia
ORDER BY DESC(?totalReis)
```

#### Lista os descobrimentos (sua descrição) por ordem cronológica.

```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?d ?data ?comment WHERE {
  ?d a ex:Descobrimento .
  ?d :data ?data .
  ?d :notas ?comment
}order by (?data)
```

#### Lista as várias conquistas, nome e data, com o nome do rei que reinava no momento.

```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?data ?nome ?rei WHERE {
  ?conquista a ex:Conquista .
  ?conquista :data ?data .
  ?conquista :nome ?nome .
  ?conquista :temReinado ?reinado  .
  ?reinado :temMonarca ?monarca .
  ?monarca :nome ?rei .
}order by (?data)
```

#### Calcula uma tabela com o nome, data de nascimento e número de mandatos de todos os presidentes portugueses.

```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?nome ?nascimento ?começo ?fim WHERE {
  ?p a ex:Presidente .
  ?p :nome ?nome .
  ?p :nascimento ?nascimento .
  ?p :mandato ?mandato .
  ?mandato :comeco ?começo .
  ?mandato :fim ?fim .
}
```

#### Quantos mandatos teve o presidente Sidónio Pais? Em que datas iniciaram e terminaram esses mndatos?

```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?nome (COUNT(?mandato) AS ?total) ?começo ?fim WHERE {
  ?p a ex:Presidente .
  ?p :nome ?nome .
  ?p :mandato ?mandato .
  ?mandato :comeco ?começo .
  ?mandato :fim ?fim .
	
  FILTER(REGEX(?nome, "^Sidónio( [A-Z][a-z]*)* Pais$", "i"))
}
GROUP BY ?nome ?começo ?fim
```
#### Quais os nomes dos partidos politicos presentes na ontologia?

```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?partido WHERE {
  ?p a ex:Partido .
  ?p :nome ?partido .
}
GROUP BY ?partido
```
#### Qual a distribuição dos militantes por cada partido politico?
```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT  ?nome (COUNT(?militante) AS ?total) WHERE {
  ?p a ex:Partido .
  ?p :temMilitante ?militante .
  ?p :nome ?nome
}
GROUP BY ?nome

```
#### Qual o partido com maior número de presidentes militantes?

```
PREFIX : <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>
PREFIX ex: <http://www.semanticweb.org/andre/ontologies/2015/6/historia#>

SELECT ?nome (COUNT(?militante) AS ?total) WHERE {
  ?p a ex:Partido .
  ?p :temMilitante ?militante .
  ?p :nome ?nome
}
GROUP BY ?nome
ORDER BY DESC(?total)
LIMIT 1
```