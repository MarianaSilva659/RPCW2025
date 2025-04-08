from rdflib import Graph, Namespace
from rdflib.namespace import RDF

g = Graph()
g.parse("med_doencas.ttl", format="turtle")

ns = Namespace("http://www.example.org/disease-ontology#") 

query1 = """
SELECT (COUNT(?doenca) AS ?numeroDoencas)
WHERE {
  ?doenca a :Disease .
}
"""

query2 = """
SELECT ?doenca
WHERE {
  ?doenca a :Disease ;
          :hasSymptom :yellowish_skin .
}
"""

query3 = """
SELECT ?doenca
WHERE {
  ?doenca a :Disease ;
          :hasTreatment :exercise .
}
"""

query4 = """
SELECT ?nome
WHERE {
  ?doente a :Patient ;
          :name ?nome .
}
ORDER BY ?nome
"""

print("Quantas doenças estão presentes na ontologia?")
for row in g.query(query1, initNs={"rdf": RDF, "": ns}):
    print("→ Número de doenças:", row.numeroDoencas)

print("\nDoenças associadas ao sintoma 'yellowish_skin':")
for row in g.query(query2, initNs={"": ns}):
    print("→", row.doenca)

print("\nDoenças associadas ao tratamento 'exercise':")
for row in g.query(query3, initNs={"": ns}):
    print("→", row.doenca)

#print("\nLista de nomes dos doentes (ordenada):")
#for row in g.query(query4, initNs={"": ns}):
#    print("→", row.nome)
