# TPC 5

Este tpc consiste em gerar uma ontologia em RDF para representar dados sobre filmes, incluindo informações sobre pessoas envolvidas, géneros, países de origem, línguas e filmes em si.

## Descrição

O código Python processa um arquivo JSON (`movies.json`) contendo informações sobre filmes e gera um arquivo de saída (`output.txt`) em formato RDF. O RDF gerado segue um modelo ontológico que representa:

- **Pessoas**: Representadas como indivíduos da classe `Pessoa`.
- **Géneros**: Representados como indivíduos da classe `Género`.
- **Países**: Representados como indivíduos da classe `País`.
- **Línguas**: Representadas como indivíduos da classe `Língua`.
- **Filmes**: Representados como indivíduos da classe `Filme`, com propriedades como título, ano, duração, língua original, país de origem e género.

## Como Funciona

1. **Leitura do Arquivo JSON**: O script lê o arquivo `movies.json` contendo dados sobre filmes.
2. **Formatação e Geração de Identificadores**: O nome das pessoas e outros dados são formatados para criar identificadores válidos no formato RDF.
3. **Criação da Ontologia**: Para cada filme, o script cria as declarações RDF para representar:
   - Pessoas (e seus nomes),
   - Géneros (e suas associações com os filmes),
   - Países de origem e línguas.
4. **Geração do Arquivo de Saída**: O resultado é um arquivo `output.txt` contendo o RDF gerado.

## Exemplo de Saída

```rdf
### http://www.semanticweb.org/mariana/ontologies/cinema#Inception
:Inception rdf:type owl:NamedIndividual , :Filme ;
           :temArgumento :ArgumentoInception ;
           :temGénero :SciFi , :Thriller ;
           :temLíngua :English ;
           :temPaisOrigem :USA ;
           :data "2010" ;
           :duração "148"^^xsd:int .
