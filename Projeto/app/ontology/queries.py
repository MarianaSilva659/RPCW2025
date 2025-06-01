from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS
from SPARQLWrapper import SPARQLWrapper, JSON, POST
import requests
import re


class OntologyQueries:
    def __init__(
        self,
        use_graphdb=True,
        graphdb_url="http://localhost:7200/repositories/space-ontology",
    ):
        self.use_graphdb = use_graphdb
        self.graphdb_url = graphdb_url

        if use_graphdb:
            self.sparql = SPARQLWrapper(f"{graphdb_url}")
            self.sparql.setReturnFormat(JSON)
            self.g = Graph()
        else:
            self.g = Graph()

        self.SPACE = Namespace("http://www.semanticweb.org/ontologies/space#")
        self.g.bind("space", self.SPACE)

    def is_update_query(self, query_string):
        cleaned_query = re.sub(r"#.*?\n", "\n", query_string)
        cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()

        tokens = cleaned_query.upper().split()

        update_keywords = [
            "INSERT",
            "DELETE",
            "CLEAR",
            "DROP",
            "CREATE",
            "LOAD",
            "COPY",
            "MOVE",
            "ADD",
        ]

        for token in tokens:
            if token in update_keywords:
                return True
        return False

    def execute_sparql_query(self, query_string):
        try:
            if self.use_graphdb:
                is_update = self.is_update_query(query_string)

                print(f"Query type detected: {'UPDATE' if is_update else 'SELECT'}")
                print(f"Query: {query_string}")

                if is_update:
                    try:
                        print("Executing UPDATE query...")

                        headers = {
                            "Content-Type": "application/sparql-update",
                            "Accept": "text/plain",
                        }

                        response = requests.post(
                            f"{self.graphdb_url}/statements",
                            data=query_string,
                            headers=headers,
                            timeout=30,
                        )

                        print(f"Update response status: {response.status_code}")
                        print(f"Update response text: {response.text}")

                        if response.status_code in [200, 204]:
                            return {
                                "success": True,
                                "message": f"Update executed successfully. Status: {response.status_code}",
                                "results": [],
                                "variables": [],
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"Update failed with status {response.status_code}: {response.text}",
                            }

                    except Exception as e:
                        print(f"Exception during update: {str(e)}")
                        return {"success": False, "error": str(e)}

                else:
                    print("Executing SELECT query...")

                    try:
                        headers = {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/sparql-results+json",
                        }

                        data = {"query": query_string}

                        response = requests.post(
                            f"{self.graphdb_url}",
                            data=data,
                            headers=headers,
                            timeout=30,
                        )

                        print(f"SELECT response status: {response.status_code}")

                        if response.status_code == 200:
                            results = response.json()
                            print(f"SELECT results: {results}")
                        else:
                            print(f"SELECT failed: {response.text}")
                            return {
                                "success": False,
                                "error": f"Query failed: {response.text}",
                            }

                    except Exception as e:
                        print(f"Exception during SELECT: {str(e)}")
                        return {"success": False, "error": str(e)}

                    formatted_results = []
                    if "results" in results and "bindings" in results["results"]:
                        for binding in results["results"]["bindings"]:
                            result = {}
                            for var, value in binding.items():
                                if value["type"] == "uri":
                                    label = self.get_label(URIRef(value["value"]))
                                    result[var] = {
                                        "uri": value["value"],
                                        "label": label,
                                    }
                                else:
                                    result[var] = value["value"]
                            formatted_results.append(result)

                    return {
                        "success": True,
                        "results": formatted_results,
                        "variables": results.get("head", {}).get("vars", []),
                    }
            else:
                results = []
                qres = self.g.query(query_string)

                for row in qres:
                    result = {}
                    for var in qres.vars:
                        value = row[var]
                        if value:
                            if isinstance(value, URIRef):
                                label = self.get_label(value)
                                result[var] = {"uri": str(value), "label": label}
                            else:
                                result[var] = (
                                    value.value
                                    if hasattr(value, "value")
                                    else str(value)
                                )
                        else:
                            result[var] = None
                    results.append(result)

                return {
                    "success": True,
                    "results": results,
                    "variables": [str(var) for var in qres.vars],
                }

        except Exception as e:
            print(f"General exception: {str(e)}")
            return {"success": False, "error": str(e)}

    def _reload_local_graph(self):
        pass

    def get_all_classes(self):
        if self.use_graphdb:
            query = """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?class ?label WHERE {
                ?class a owl:Class .
                OPTIONAL { ?class rdfs:label ?label }
            }
            """

            try:
                self.sparql.setQuery(query)
                results = self.sparql.query().convert()

                classes = []
                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        class_uri = binding["class"]["value"]
                        label = binding.get("label", {}).get(
                            "value", class_uri.split("#")[-1]
                        )
                        classes.append({"uri": class_uri, "label": label})

                return classes
            except Exception as e:
                print(f"Error in get_all_classes: {e}")
                return []
        else:
            classes = []
            for s, p, o in self.g.triples((None, RDF.type, None)):
                if str(o) == "http://www.w3.org/2002/07/owl#Class":
                    class_uri = str(s)
                    label = self.get_label(s)
                    classes.append({"uri": class_uri, "label": label})
            return classes

    def get_label(self, uri):
        if not uri:
            return "Unknown"

        if "#" in str(uri):
            return str(uri).split("#")[-1]
        return str(uri)

    def get_instances_of_class(self, class_uri):
        if self.use_graphdb:
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX space: <http://www.semanticweb.org/ontologies/space#>
            
            SELECT ?instance ?label WHERE {{
                ?instance a <{class_uri}> .
                OPTIONAL {{ ?instance rdfs:label ?label }}
                OPTIONAL {{ ?instance space:name ?label }}
            }}
            """

            try:
                self.sparql.setQuery(query)
                results = self.sparql.query().convert()

                instances = []
                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        instance_uri = binding["instance"]["value"]
                        label = binding.get("label", {}).get(
                            "value", instance_uri.split("#")[-1]
                        )
                        instances.append({"uri": instance_uri, "label": label})

                return instances
            except Exception as e:
                print(f"Error in get_instances_of_class: {e}")
                return []
        else:
            instances = []
            try:
                class_uri = (
                    URIRef(class_uri)
                    if not isinstance(class_uri, URIRef)
                    else class_uri
                )

                for s, p, o in self.g.triples((None, RDF.type, class_uri)):
                    instance_uri = str(s)
                    label = self.get_label(s)
                    instances.append({"uri": instance_uri, "label": label})
            except Exception as e:
                print(f"Error in get_instances_of_class: {e}")

            return instances

    def get_instance_properties(self, instance_uri):
        if self.use_graphdb:
            properties = []
            try:
                query = f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?property ?value WHERE {{
                    <{instance_uri}> ?property ?value .
                    FILTER(?property != rdf:type && ?property != rdfs:label)
                }}
                """

                self.sparql.setQuery(query)
                results = self.sparql.query().convert()

                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        prop_uri = binding["property"]["value"]
                        prop_name = (
                            prop_uri.split("#")[-1] if "#" in prop_uri else prop_uri
                        )

                        value = binding["value"]["value"]
                        if binding["value"]["type"] == "uri":
                            label = self.get_label(value)
                            value = label if label != "Unknown" else value

                        properties.append({"property": prop_name, "value": value})

            except Exception as e:
                print(f"Error in get_instance_properties: {e}")
            return properties
        else:
            properties = []
            try:
                instance_uri = (
                    URIRef(instance_uri)
                    if not isinstance(instance_uri, URIRef)
                    else instance_uri
                )

                for s, p, o in self.g.triples((instance_uri, None, None)):
                    if p != RDF.type and p != RDFS.label:
                        prop_name = str(p).split("#")[-1]

                        obj_value = o.value if hasattr(o, "value") else str(o)
                        if isinstance(o, URIRef):
                            obj_label = self.get_label(o)
                            if obj_label:
                                obj_value = obj_label

                        properties.append({"property": prop_name, "value": obj_value})
            except Exception as e:
                print(f"Error in get_instance_properties: {e}")

            return properties

    def search_by_name(self, search_term):
        if self.use_graphdb:
            query = f"""
            PREFIX space: <http://www.semanticweb.org/ontologies/space#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?instance ?name ?type WHERE {{
                ?instance space:name ?name .
                ?instance a ?type .
                FILTER(CONTAINS(LCASE(?name), LCASE("{search_term}")))
                FILTER(?type != <http://www.w3.org/2002/07/owl#Class>)
            }}
            """

            try:
                self.sparql.setQuery(query)
                results = self.sparql.query().convert()

                search_results = []
                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        instance_uri = binding["instance"]["value"]
                        name = binding["name"]["value"]
                        type_uri = binding["type"]["value"]
                        type_name = (
                            type_uri.split("#")[-1] if "#" in type_uri else type_uri
                        )

                        search_results.append(
                            {
                                "uri": instance_uri,
                                "name": name,
                                "type": type_name,
                            }
                        )

                return search_results
            except Exception as e:
                print(f"Error in search_by_name: {e}")
                return []
        else:
            results = []
            try:
                for s, p, o in self.g.triples((None, self.SPACE.name, None)):
                    if search_term.lower() in str(o).lower():
                        instance_uri = str(s)
                        instance_name = o.value

                        instance_type = None
                        for _, _, type_uri in self.g.triples((s, RDF.type, None)):
                            if "#" in str(type_uri):
                                instance_type = str(type_uri).split("#")[-1]
                                break

                        results.append(
                            {
                                "uri": instance_uri,
                                "name": instance_name,
                                "type": instance_type,
                            }
                        )
            except Exception as e:
                print(f"Error in search_by_name: {e}")

            return results

    def get_relationships(self, instance_uri):
        if self.use_graphdb:
            relationships = []
            seen_relationships = set()

            try:
                outgoing_query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX space: <http://www.semanticweb.org/ontologies/space#>
                
                SELECT DISTINCT ?property ?target ?targetLabel ?targetType WHERE {{
                    <{instance_uri}> ?property ?target .
                    FILTER(isURI(?target) && ?property != rdf:type)
                    
                    OPTIONAL {{ ?target rdfs:label ?targetLabel }}
                    OPTIONAL {{ ?target space:name ?targetLabel }}
                    OPTIONAL {{ ?target rdf:type ?targetType }}
                }}
                """

                self.sparql.setQuery(outgoing_query)
                results = self.sparql.query().convert()

                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        rel_type = binding["property"]["value"].split("#")[-1]
                        target_uri = binding["target"]["value"]
                        target_label = binding.get("targetLabel", {}).get(
                            "value", target_uri.split("#")[-1]
                        )
                        target_type = (
                            binding.get("targetType", {})
                            .get("value", "")
                            .split("#")[-1]
                            if binding.get("targetType")
                            else None
                        )

                        rel_key = f"out:{rel_type}:{target_uri}"
                        if rel_key not in seen_relationships:
                            seen_relationships.add(rel_key)
                            relationships.append(
                                {
                                    "direction": "outgoing",
                                    "type": rel_type,
                                    "target_uri": target_uri,
                                    "target_label": target_label,
                                    "target_type": target_type,
                                }
                            )

                incoming_query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX space: <http://www.semanticweb.org/ontologies/space#>
                
                SELECT DISTINCT ?property ?source ?sourceLabel ?sourceType WHERE {{
                    ?source ?property <{instance_uri}> .
                    FILTER(?property != rdf:type)
                    
                    OPTIONAL {{ ?source rdfs:label ?sourceLabel }}
                    OPTIONAL {{ ?source space:name ?sourceLabel }}
                    OPTIONAL {{ ?source rdf:type ?sourceType }}
                }}
                """

                self.sparql.setQuery(incoming_query)
                results = self.sparql.query().convert()

                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        rel_type = binding["property"]["value"].split("#")[-1]
                        source_uri = binding["source"]["value"]
                        source_label = binding.get("sourceLabel", {}).get(
                            "value", source_uri.split("#")[-1]
                        )
                        source_type = (
                            binding.get("sourceType", {})
                            .get("value", "")
                            .split("#")[-1]
                            if binding.get("sourceType")
                            else None
                        )

                        rel_key = f"in:{rel_type}:{source_uri}"
                        if rel_key not in seen_relationships:
                            seen_relationships.add(rel_key)
                            relationships.append(
                                {
                                    "direction": "incoming",
                                    "type": rel_type,
                                    "source_uri": source_uri,
                                    "source_label": source_label,
                                    "source_type": source_type,
                                }
                            )

            except Exception as e:
                print(f"Error in get_relationships: {e}")

            return relationships
        else:
            relationships = []
            seen_relationships = set()

            try:
                instance_uri = (
                    URIRef(instance_uri)
                    if not isinstance(instance_uri, URIRef)
                    else instance_uri
                )

                for s, p, o in self.g.triples((instance_uri, None, None)):
                    if isinstance(o, URIRef) and p != RDF.type:
                        rel_type = str(p).split("#")[-1]
                        target_label = self.get_label(o)
                        target_type = None

                        for _, _, type_uri in self.g.triples((o, RDF.type, None)):
                            if "#" in str(type_uri):
                                target_type = str(type_uri).split("#")[-1]
                                break

                        rel_key = f"out:{rel_type}:{str(o)}"
                        if rel_key not in seen_relationships:
                            seen_relationships.add(rel_key)
                            relationships.append(
                                {
                                    "direction": "outgoing",
                                    "type": rel_type,
                                    "target_uri": str(o),
                                    "target_label": target_label,
                                    "target_type": target_type,
                                }
                            )

                for s, p, o in self.g.triples((None, None, instance_uri)):
                    if p != RDF.type:
                        rel_type = str(p).split("#")[-1]
                        source_label = self.get_label(s)
                        source_type = None

                        for _, _, type_uri in self.g.triples((s, RDF.type, None)):
                            if "#" in str(type_uri):
                                source_type = str(type_uri).split("#")[-1]
                                break

                        rel_key = f"in:{rel_type}:{str(s)}"
                        if rel_key not in seen_relationships:
                            seen_relationships.add(rel_key)
                            relationships.append(
                                {
                                    "direction": "incoming",
                                    "type": rel_type,
                                    "source_uri": str(s),
                                    "source_label": source_label,
                                    "source_type": source_type,
                                }
                            )
            except Exception as e:
                print(f"Error in get_relationships: {e}")

            return relationships

    def get_statistics(self):
        stats = {
            "total_triples": 0,
            "classes": {},
            "properties": {"object_properties": 0, "data_properties": 0},
        }

        try:
            if self.use_graphdb:
                count_query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
                self.sparql.setQuery(count_query)
                results = self.sparql.query().convert()

                if "results" in results and "bindings" in results["results"]:
                    bindings = results["results"]["bindings"]
                    if bindings:
                        stats["total_triples"] = int(bindings[0]["count"]["value"])

                class_query = """
                SELECT ?type (COUNT(?instance) as ?count) WHERE {
                    ?instance a ?type .
                    FILTER(?type != <http://www.w3.org/2002/07/owl#Class>)
                    FILTER(?type != <http://www.w3.org/2002/07/owl#ObjectProperty>)
                    FILTER(?type != <http://www.w3.org/2002/07/owl#DatatypeProperty>)
                } GROUP BY ?type
                """

                self.sparql.setQuery(class_query)
                results = self.sparql.query().convert()

                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        type_uri = binding["type"]["value"]
                        count = int(binding["count"]["value"])
                        class_name = (
                            type_uri.split("#")[-1] if "#" in type_uri else type_uri
                        )
                        stats["classes"][class_name] = count
            else:
                stats["total_triples"] = len(self.g)

                for s, p, o in self.g.triples((None, RDF.type, None)):
                    if "#" in str(o):
                        class_name = str(o).split("#")[-1]
                        if class_name not in stats["classes"]:
                            stats["classes"][class_name] = 0
                        stats["classes"][class_name] += 1

                for s, p, o in self.g.triples((None, RDF.type, None)):
                    if str(o) == "http://www.w3.org/2002/07/owl#ObjectProperty":
                        stats["properties"]["object_properties"] += 1
                    elif str(o) == "http://www.w3.org/2002/07/owl#DatatypeProperty":
                        stats["properties"]["data_properties"] += 1

        except Exception as e:
            print(f"Error in get_statistics: {e}")

        return stats

    def get_graph_data(self, limit_per_type=25, class_filter=None):
        if self.use_graphdb:
            nodes = []
            links = []
            node_ids = set()

            try:
                classes_query = """
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX space: <http://www.semanticweb.org/ontologies/space#>
                
                SELECT ?class ?label WHERE {
                    ?class a owl:Class .
                    FILTER(STRSTARTS(STR(?class), STR(space:)))
                    OPTIONAL { ?class rdfs:label ?label }
                }
                """

                self.sparql.setQuery(classes_query)
                results = self.sparql.query().convert()

                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        class_uri = binding["class"]["value"]
                        label = binding.get("label", {}).get(
                            "value", class_uri.split("#")[-1]
                        )
                        nodes.append({"id": class_uri, "label": label, "type": "class"})
                        node_ids.add(class_uri)

                space_classes = [
                    "Planet",
                    "Star",
                    "Moon",
                    "Asteroid",
                    "Comet",
                    "Galaxy",
                    "SpaceMission",
                    "Astronaut",
                    "SpaceAgency",
                    "Spacecraft",
                ]

                if class_filter and class_filter in space_classes:
                    space_classes = [class_filter]

                for class_name in space_classes:
                    instances_query = f"""
                    PREFIX space: <http://www.semanticweb.org/ontologies/space#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    
                    SELECT ?instance ?label WHERE {{
                        ?instance a space:{class_name} .
                        OPTIONAL {{ ?instance rdfs:label ?label }}
                        OPTIONAL {{ ?instance space:name ?label }}
                    }}
                    LIMIT {limit_per_type}
                    """

                    self.sparql.setQuery(instances_query)
                    results = self.sparql.query().convert()

                    if "results" in results and "bindings" in results["results"]:
                        class_uri = (
                            f"http://www.semanticweb.org/ontologies/space#{class_name}"
                        )

                        for binding in results["results"]["bindings"]:
                            instance_uri = binding["instance"]["value"]
                            label = binding.get("label", {}).get(
                                "value", instance_uri.split("#")[-1]
                            )

                            nodes.append(
                                {
                                    "id": instance_uri,
                                    "label": label,
                                    "type": class_name,
                                }
                            )
                            node_ids.add(instance_uri)

                            if class_uri in node_ids:
                                links.append(
                                    {
                                        "source": instance_uri,
                                        "target": class_uri,
                                        "label": "type",
                                    }
                                )

                relationships_query = f"""
                PREFIX space: <http://www.semanticweb.org/ontologies/space#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                
                SELECT ?source ?property ?target WHERE {{
                    ?source ?property ?target .
                    FILTER(isURI(?target) && ?property != rdf:type && ?property != rdfs:subClassOf)
                    FILTER(STRSTARTS(STR(?source), STR(space:)) && STRSTARTS(STR(?target), STR(space:)))
                }}
                LIMIT 500
                """

                self.sparql.setQuery(relationships_query)
                results = self.sparql.query().convert()

                if "results" in results and "bindings" in results["results"]:
                    for binding in results["results"]["bindings"]:
                        source_id = binding["source"]["value"]
                        target_id = binding["target"]["value"]
                        property_uri = binding["property"]["value"]

                        if source_id in node_ids and target_id in node_ids:
                            rel_type = property_uri.split("#")[-1]
                            links.append(
                                {
                                    "source": source_id,
                                    "target": target_id,
                                    "label": rel_type,
                                }
                            )

            except Exception as e:
                print(f"Error in get_graph_data: {e}")

            return {"nodes": nodes, "links": links}
        else:
            nodes = []
            links = []
            node_ids = set()

            try:
                for s, p, o in self.g.triples((None, RDF.type, None)):
                    if str(o) == "http://www.w3.org/2002/07/owl#Class":
                        node_id = str(s)
                        if node_id not in node_ids:
                            nodes.append(
                                {
                                    "id": node_id,
                                    "label": self.get_label(s),
                                    "type": "class",
                                }
                            )
                            node_ids.add(node_id)

                instance_types = {}
                for s, p, o in self.g.triples((None, RDF.type, None)):
                    if (
                        str(o) != "http://www.w3.org/2002/07/owl#Class"
                        and str(o) != "http://www.w3.org/2002/07/owl#ObjectProperty"
                        and str(o) != "http://www.w3.org/2002/07/owl#DatatypeProperty"
                    ):

                        type_name = str(o).split("#")[-1]
                        if type_name not in instance_types:
                            instance_types[type_name] = []

                        instance_uri = str(s)
                        instance_types[type_name].append(instance_uri)

                if class_filter:
                    filtered_types = {}
                    for type_name, instances in instance_types.items():
                        if type_name == class_filter:
                            filtered_types[type_name] = instances
                    instance_types = filtered_types

                for type_name, instances in instance_types.items():
                    type_uri = None
                    for s, p, o in self.g.triples((None, RDF.type, None)):
                        if str(o) == "http://www.w3.org/2002/07/owl#Class" and str(
                            s
                        ).endswith("#" + type_name):
                            type_uri = str(s)
                            break

                    for instance_uri in instances[:limit_per_type]:
                        if instance_uri not in node_ids:
                            s = URIRef(instance_uri)
                            nodes.append(
                                {
                                    "id": instance_uri,
                                    "label": self.get_label(s),
                                    "type": type_name,
                                }
                            )
                            node_ids.add(instance_uri)

                            if type_uri:
                                links.append(
                                    {
                                        "source": instance_uri,
                                        "target": type_uri,
                                        "label": "type",
                                    }
                                )

                for s, p, o in self.g.triples((None, None, None)):
                    if (
                        isinstance(s, URIRef)
                        and isinstance(o, URIRef)
                        and p != RDF.type
                        and p != RDFS.subClassOf
                    ):

                        source_id = str(s)
                        target_id = str(o)

                        if source_id in node_ids and target_id in node_ids:
                            rel_type = str(p).split("#")[-1]
                            links.append(
                                {
                                    "source": source_id,
                                    "target": target_id,
                                    "label": rel_type,
                                }
                            )

            except Exception as e:
                print(f"Error in get_graph_data: {e}")

            return {"nodes": nodes, "links": links}
