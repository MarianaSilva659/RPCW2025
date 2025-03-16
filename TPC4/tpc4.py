import json
from graphdb import query_graphdb
from urllib.parse import urlparse

endpoint = "http://dbpedia.org/sparql"
dataset = []

sparql_films = """
SELECT DISTINCT ?film
WHERE {
    ?film a dbo:Film .
}
LIMIT 100
"""

def extract_name_from_url(url):
    return urlparse(url).path.split('/')[-1].replace('_', ' ')

try:
    films_result = query_graphdb(endpoint, sparql_films)
    if films_result is None:
        raise ValueError("No results returned from the SPARQL endpoint.")
    films = [film["film"]["value"] for film in films_result.get("results", {}).get("bindings", [])]
except Exception as e:
    print(f"Error querying films: {e}")
    films = []

for film in films:
    sparql_query = f"""
    SELECT DISTINCT ?title ?country ?releaseDate ?director ?abstract
    WHERE {{
        <{film}> dbo:abstract ?abstract .
        <{film}> rdfs:label ?title .
        OPTIONAL {{ <{film}> dbo:country ?country . }}
        OPTIONAL {{ <{film}> dbo:releaseDate ?releaseDate . }}
        OPTIONAL {{ <{film}> dbo:director ?director . }}
        FILTER (lang(?abstract) = "en") .
        FILTER (lang(?title) = "en") .
    }}
    """

    result = query_graphdb(endpoint, sparql_query)
    print("result ", result)  # Corrected indentation

    sparql_query2 = f"""
    SELECT DISTINCT ?actor ?name ?birthDate ?nationality
    WHERE {{
        <{film}> dbo:starring ?actor .
        OPTIONAL {{ ?actor rdfs:label ?name . FILTER (lang(?name) = "en") . }}
        OPTIONAL {{ ?actor dbo:birthDate ?birthDate . }}
        OPTIONAL {{ ?actor dbo:nationality ?nationality . }}
    }}
    """

    result2 = query_graphdb(endpoint, sparql_query2)
    print("result 2", result2)  # Corrected indentation

    cast = []
    for actor in result2.get("results", {}).get("bindings", []):
        cast.append(
            {
                "id": extract_name_from_url(actor.get("actor", {}).get("value", "")),
                "nome": actor.get("name", {}).get("value", ""),
                "dataNasc": actor.get("birthDate", {}).get("value", ""),
                "origem": actor.get("nationality", {}).get("value", "")
            }
        )

    sparql_query3 = f"""
    SELECT DISTINCT ?genreLabel
    WHERE {{
        <{film}> dbo:genre ?genre .
        ?genre rdfs:label ?genreLabel .
        FILTER (lang(?genreLabel) = "en") .
    }}
    """

    result3 = query_graphdb(endpoint, sparql_query3)
    print("result 3", result3)  # Corrected indentation

    genres = [g["genreLabel"]["value"] for g in result3.get("results", {}).get("bindings", [])]

    if result["results"]["bindings"]:
        binding = result["results"]["bindings"][0]
        dataset.append(
            {
                "id": extract_name_from_url(film),
                "titulo": binding["title"]["value"],
                "pais": extract_name_from_url(binding.get("country", {}).get("value", "")),
                "data": binding.get("releaseDate", {}).get("value", ""),
                "realizador": extract_name_from_url(binding.get("director", {}).get("value", "")),
                "elenco": cast,
                "genero": genres,
                "sinopse": binding["abstract"]["value"]
            }
        )
    else:
        dataset.append(
            {
                "id": extract_name_from_url(film),
                "titulo": "",
                "pais": "",
                "data": "",
                "realizador": "",
                "elenco": cast,
                "genero": genres,
                "sinopse": ""
            }
        )

with open('movies.json', 'w') as f:
    json.dump(dataset, f, indent=4)

print("Dataset saved as films_dataset.json")
