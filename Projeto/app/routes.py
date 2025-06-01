from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_file,
)
from app.ontology.creator import OntologyCreator
from app.ontology.queries import OntologyQueries
import os
import requests
from rdflib import URIRef
from rdflib.namespace import RDF
from werkzeug.utils import secure_filename

main = Blueprint("main", __name__)

CURRENT_GRAPHDB_CONFIG = {
    "host": "localhost",
    "port": 7200,
    "repository": "Not Selected",
}


def create_graphdb_repository(repository_url, repository_name):
    config_ttl = f"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep: <http://www.openrdf.org/config/repository#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix graphdb: <http://www.ontotext.com/config/graphdb#> .

[] a rep:Repository ;
   rep:repositoryID "{repository_name}" ;
   rdfs:label "{repository_name}" ;
   rep:repositoryImpl [
      rep:repositoryType "graphdb:SailRepository" ;
      sr:sailImpl [
         sail:sailType "graphdb:Sail" ;
         graphdb:ruleset "rdfsplus-optimized" ;
         graphdb:storage-folder "storage" ;
         graphdb:enable-context-index true ;
         graphdb:enablePredicateList true ;
         graphdb:enable-literal-index true ;
         graphdb:in-memory-literal-properties false ;
         graphdb:base-URL "http://example.org/ontology#" ;
         graphdb:repository-type "file-repository"
      ]
   ] .
"""

    files = {"config": (f"{repository_name}.ttl", config_ttl, "text/turtle")}

    try:
        response = requests.post(
            f"{repository_url}/rest/repositories", files=files, timeout=30
        )

        if response.status_code == 201:
            return {
                "success": True,
                "message": f"Repository '{repository_name}' created successfully",
            }
        elif response.status_code == 409:
            return {
                "success": True,
                "message": f"Repository '{repository_name}' already exists",
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create repository. Status: {response.status_code}. {response.text}",
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Connection error while creating repository: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while creating repository: {str(e)}",
        }


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/management")
def management():
    return render_template("management.html")


@main.route("/explore")
def explore():
    return render_template("explore.html")


@main.route("/entity")
def entity_page():
    return render_template("entity.html")


@main.route("/sparql")
def sparql():
    return render_template("sparql.html")


@main.route("/graph")
def graph():
    return render_template("graph.html")


@main.route("/api/config", methods=["GET", "POST"])
def manage_config():
    global CURRENT_GRAPHDB_CONFIG

    if request.method == "POST":
        data = request.json
        if data:
            CURRENT_GRAPHDB_CONFIG.update(data)
        return jsonify({"status": "success", "config": CURRENT_GRAPHDB_CONFIG})
    else:
        return jsonify(CURRENT_GRAPHDB_CONFIG)


@main.route("/api/graphdb/test-connection", methods=["POST"])
def test_graphdb_connection():
    try:
        data = request.json
        host = data.get("host", "localhost")
        port = data.get("port", 7200)

        test_url = f"http://{host}:{port}/rest/repositories"
        response = requests.get(test_url, timeout=5)

        if response.status_code == 200:
            return jsonify(
                {
                    "status": "success",
                    "message": "GraphDB connection established successfully",
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"GraphDB server responded with status {response.status_code}. Please check if GraphDB is running.",
                    }
                ),
                400,
            )

    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Unable to connect to GraphDB: {str(e)}",
                }
            ),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Connection test failed: {str(e)}"}
            ),
            500,
        )


@main.route("/api/graphdb/repositories", methods=["GET"])
def list_repositories():
    try:
        host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])

        url = f"http://{host}:{port}/rest/repositories"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            repositories = response.json()
            return jsonify({"status": "success", "repositories": repositories})
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Unable to fetch repositories from GraphDB. Server responded with status {response.status_code}.",
                    }
                ),
                400,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error retrieving repositories: {str(e)}",
                }
            ),
            500,
        )


@main.route("/api/graphdb/create-repository", methods=["POST"])
def create_repository():
    try:
        data = request.json
        host = data.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = data.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repo_name = data.get("repository")

        if not repo_name:
            return (
                jsonify({"status": "error", "message": "Repository name is required"}),
                400,
            )

        if not repo_name.strip():
            return (
                jsonify(
                    {"status": "error", "message": "Repository name cannot be empty"}
                ),
                400,
            )

        repository_url = f"http://{host}:{port}"
        result = create_graphdb_repository(repository_url, repo_name)

        if result["success"]:
            return jsonify({"status": "success", "message": result["message"]})
        else:
            return jsonify({"status": "error", "message": result["message"]}), 400

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Repository creation failed: {str(e)}"}
            ),
            500,
        )


@main.route("/api/create-repository-and-select", methods=["POST"])
def create_repository_and_select():
    global CURRENT_GRAPHDB_CONFIG

    try:
        data = request.json
        host = data.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = data.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repo_name = data.get("repository")

        if not repo_name:
            return (
                jsonify({"status": "error", "message": "Repository name is required"}),
                400,
            )

        if not repo_name.strip():
            return (
                jsonify(
                    {"status": "error", "message": "Repository name cannot be empty"}
                ),
                400,
            )

        repository_url = f"http://{host}:{port}"
        result = create_graphdb_repository(repository_url, repo_name)

        if result["success"]:
            CURRENT_GRAPHDB_CONFIG.update(
                {"host": host, "port": port, "repository": repo_name}
            )

            return jsonify(
                {
                    "status": "success",
                    "message": result["message"],
                    "config": CURRENT_GRAPHDB_CONFIG,
                }
            )
        else:
            return jsonify({"status": "error", "message": result["message"]}), 400

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Repository creation failed: {str(e)}"}
            ),
            500,
        )


@main.route("/api/import-ontology", methods=["POST"])
def import_ontology():
    global CURRENT_GRAPHDB_CONFIG

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file selected for import"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected for import"}), 400

        host = request.form.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = int(request.form.get("port", CURRENT_GRAPHDB_CONFIG["port"]))
        repository = request.form.get(
            "repository", CURRENT_GRAPHDB_CONFIG["repository"]
        )
        create_repo = request.form.get("create_repository") == "true"
        new_repo_name = request.form.get("new_repository_name")

        if create_repo:
            if not new_repo_name:
                return (
                    jsonify(
                        {
                            "error": "Repository name is required when creating a new repository"
                        }
                    ),
                    400,
                )

            repository = new_repo_name.strip()
            if not repository:
                return jsonify({"error": "Repository name cannot be empty"}), 400

            repository_url = f"http://{host}:{port}"
            result = create_graphdb_repository(repository_url, repository)
            if not result["success"]:
                return (
                    jsonify(
                        {"error": f"Failed to create repository: {result['message']}"}
                    ),
                    500,
                )

            CURRENT_GRAPHDB_CONFIG.update(
                {"host": host, "port": port, "repository": repository}
            )
        else:
            if repository == "Not Selected":
                return (
                    jsonify({"error": "Please select a repository before importing"}),
                    400,
                )

        if file:
            filename = secure_filename(file.filename)
            temp_path = os.path.join("temp", filename)

            os.makedirs("temp", exist_ok=True)
            file.save(temp_path)

            graphdb_url = f"http://{host}:{port}/repositories/{repository}"

            with open(temp_path, "rb") as f:
                headers = {"Content-Type": "text/turtle", "Accept": "application/json"}

                response = requests.post(
                    f"{graphdb_url}/statements", data=f, headers=headers, timeout=60
                )

            os.remove(temp_path)

            if response.status_code in [200, 201, 204]:
                return jsonify(
                    {
                        "status": "success",
                        "message": "Ontology imported successfully to GraphDB",
                        "config": CURRENT_GRAPHDB_CONFIG,
                    }
                )
            else:
                return (
                    jsonify({"error": f"GraphDB import failed: {response.text}"}),
                    500,
                )

    except Exception as e:
        return jsonify({"error": f"Import operation failed: {str(e)}"}), 500


@main.route("/api/export-ontology")
def export_ontology():
    try:
        host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = request.args.get(
            "repository", CURRENT_GRAPHDB_CONFIG["repository"]
        )

        if repository == "Not Selected":
            return (
                jsonify({"error": "Please select a repository before exporting"}),
                400,
            )

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"

        headers = {"Accept": "text/turtle"}
        response = requests.get(
            f"{graphdb_url}/statements", headers=headers, timeout=60
        )

        if response.status_code == 200:
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, "temp_export.ttl")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(response.text)

            return send_file(
                temp_file,
                as_attachment=True,
                download_name=f"{repository}_ontology.ttl",
                mimetype="text/turtle",
            )
        else:
            return (
                jsonify({"error": f"GraphDB export failed: {response.text}"}),
                500,
            )

    except Exception as e:
        return jsonify({"error": f"Export operation failed: {str(e)}"}), 500


@main.route("/api/create-base-ontology", methods=["POST"])
def create_base_ontology():
    global CURRENT_GRAPHDB_CONFIG

    try:
        data = request.json
        host = data.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = data.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = data.get("repository", CURRENT_GRAPHDB_CONFIG["repository"])
        create_repo = data.get("create_repository", False)
        new_repo_name = data.get("new_repository_name")

        if create_repo:
            if not new_repo_name:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Repository name is required when creating a new repository",
                        }
                    ),
                    400,
                )

            repository = new_repo_name.strip()
            if not repository:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Repository name cannot be empty",
                        }
                    ),
                    400,
                )

            repository_url = f"http://{host}:{port}"
            result = create_graphdb_repository(repository_url, repository)
            if not result["success"]:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"Repository creation failed: {result['message']}",
                        }
                    ),
                    500,
                )

            CURRENT_GRAPHDB_CONFIG.update(
                {"host": host, "port": port, "repository": repository}
            )
        else:
            if repository == "Not Selected":
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Please select a repository before creating ontology",
                        }
                    ),
                    400,
                )

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"

        try:
            creator = OntologyCreator(use_graphdb=True, graphdb_url=graphdb_url)
            creator.create_ontology_structure()
            creator.fetch_solar_system_data()
            creator.fetch_spacex_data()
            creator.fetch_nasa_data()
            creator.fetch_exoplanet_data()

            success = creator.save_ontology()

            if success:
                return jsonify(
                    {
                        "status": "success",
                        "message": "Base ontology created and populated with space data successfully",
                        "config": CURRENT_GRAPHDB_CONFIG,
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Ontology creation completed but failed to save to GraphDB",
                        }
                    ),
                    500,
                )
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Ontology creation failed: {str(e)}",
                    }
                ),
                500,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Base ontology operation failed: {str(e)}",
                }
            ),
            500,
        )


@main.route("/api/clear-repository", methods=["POST"])
def clear_repository():
    try:
        data = request.json
        host = data.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = data.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = data.get("repository", CURRENT_GRAPHDB_CONFIG["repository"])

        if repository == "Not Selected":
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Please select a repository before clearing",
                    }
                ),
                400,
            )

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"

        response = requests.delete(f"{graphdb_url}/statements", timeout=30)

        if response.status_code in [200, 204]:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Repository '{repository}' cleared successfully",
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to clear repository '{repository}': {response.text}",
                    }
                ),
                500,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Repository clear operation failed: {str(e)}",
                }
            ),
            500,
        )


@main.route("/api/delete-repository", methods=["POST"])
def delete_repository():
    try:
        data = request.json
        host = data.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = data.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = data.get("repository", CURRENT_GRAPHDB_CONFIG["repository"])

        if repository == "Not Selected":
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Please select a repository to delete",
                    }
                ),
                400,
            )

        repository_url = f"http://{host}:{port}/rest/repositories/{repository}"

        response = requests.delete(repository_url, timeout=30)

        if response.status_code in [200, 204]:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Repository '{repository}' deleted successfully",
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to delete repository '{repository}': {response.text}",
                    }
                ),
                500,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Repository deletion operation failed: {str(e)}",
                }
            ),
            500,
        )


@main.route("/api/classes")
def get_classes():
    try:
        host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = request.args.get(
            "repository", CURRENT_GRAPHDB_CONFIG["repository"]
        )

        if repository == "Not Selected":
            return jsonify({"error": "Please select a repository to view classes"}), 400

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"
        queries = OntologyQueries(use_graphdb=True, graphdb_url=graphdb_url)
        classes = queries.get_all_classes()
        return jsonify(classes)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve classes: {str(e)}"}), 500


@main.route("/api/instances")
def get_instances():
    class_uri = request.args.get("class")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 30))
    host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
    port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])
    repository = request.args.get("repository", CURRENT_GRAPHDB_CONFIG["repository"])

    if not class_uri:
        return jsonify({"error": "Class URI is required to retrieve instances"}), 400

    if repository == "Not Selected":
        return jsonify({"error": "Please select a repository to view instances"}), 400

    try:
        graphdb_url = f"http://{host}:{port}/repositories/{repository}"
        queries = OntologyQueries(use_graphdb=True, graphdb_url=graphdb_url)
        all_instances = queries.get_instances_of_class(class_uri)

        total_instances = len(all_instances)
        total_pages = (total_instances + limit - 1) // limit

        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total_instances)
        paginated_instances = all_instances[start_idx:end_idx]

        return jsonify(
            {
                "instances": paginated_instances,
                "total": total_instances,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve instances: {str(e)}"}), 500


@main.route("/api/entity")
def get_entity():
    try:
        uri = request.args.get("uri")
        if not uri:
            return jsonify({"error": "Entity URI is required"}), 400

        host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = request.args.get(
            "repository", CURRENT_GRAPHDB_CONFIG["repository"]
        )

        if repository == "Not Selected":
            return (
                jsonify({"error": "Please select a repository to view entity details"}),
                400,
            )

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"
        queries = OntologyQueries(use_graphdb=True, graphdb_url=graphdb_url)

        entity_type = None
        uri_ref = URIRef(uri)
        for s, p, o in queries.g.triples((uri_ref, RDF.type, None)):
            if "#" in str(o):
                entity_type = str(o).split("#")[-1]
                break

        label = queries.get_label(uri_ref)
        properties = queries.get_instance_properties(uri)
        relationships = queries.get_relationships(uri)

        return jsonify(
            {
                "uri": uri,
                "label": label,
                "type": entity_type,
                "properties": properties,
                "relationships": relationships,
            }
        )
    except Exception as e:
        import traceback

        print(f"Error in get_entity: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to retrieve entity details: {str(e)}"}), 500


@main.route("/api/search")
def search():
    try:
        term = request.args.get("term")
        if not term:
            return jsonify({"error": "Search term is required"}), 400

        host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = request.args.get(
            "repository", CURRENT_GRAPHDB_CONFIG["repository"]
        )

        if repository == "Not Selected":
            return (
                jsonify({"error": "Please select a repository to perform search"}),
                400,
            )

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"
        queries = OntologyQueries(use_graphdb=True, graphdb_url=graphdb_url)
        results = queries.search_by_name(term)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Search operation failed: {str(e)}"}), 500


@main.route("/api/statistics")
def get_statistics():
    try:
        host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = request.args.get(
            "repository", CURRENT_GRAPHDB_CONFIG["repository"]
        )

        if repository == "Not Selected":
            return (
                jsonify({"error": "Please select a repository to view statistics"}),
                400,
            )

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"
        queries = OntologyQueries(use_graphdb=True, graphdb_url=graphdb_url)
        stats = queries.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve statistics: {str(e)}"}), 500


@main.route("/api/sparql", methods=["POST"])
def execute_sparql():
    try:
        data = request.json
        query = data.get("query")
        if not query:
            return jsonify({"error": "SPARQL query is required"}), 400

        host = data.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = data.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = data.get("repository", CURRENT_GRAPHDB_CONFIG["repository"])

        if repository == "Not Selected":
            return (
                jsonify(
                    {"error": "Please select a repository to execute SPARQL queries"}
                ),
                400,
            )

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"
        queries = OntologyQueries(use_graphdb=True, graphdb_url=graphdb_url)
        result = queries.execute_sparql_query(query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"SPARQL query execution failed: {str(e)}"}), 500


@main.route("/api/graph-data")
def get_graph_data():
    try:
        host = request.args.get("host", CURRENT_GRAPHDB_CONFIG["host"])
        port = request.args.get("port", CURRENT_GRAPHDB_CONFIG["port"])
        repository = request.args.get(
            "repository", CURRENT_GRAPHDB_CONFIG["repository"]
        )

        if repository == "Not Selected":
            return (
                jsonify(
                    {"error": "Please select a repository to view graph visualization"}
                ),
                400,
            )

        limit_per_type = int(request.args.get("limit_per_type", 25))
        class_filter = request.args.get("class_filter")

        graphdb_url = f"http://{host}:{port}/repositories/{repository}"
        queries = OntologyQueries(use_graphdb=True, graphdb_url=graphdb_url)
        graph_data = queries.get_graph_data(
            limit_per_type=limit_per_type, class_filter=class_filter
        )
        return jsonify(graph_data)
    except Exception as e:
        return jsonify({"error": f"Failed to generate graph data: {str(e)}"}), 500
