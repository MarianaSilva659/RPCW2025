from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 80)
    print("Spatial Ontology")
    print("=" * 80)
    print("Access the application at: http://localhost:5000")
    print("To use GraphDB, configure it at: http://localhost:5000/management")
    print("=" * 80)
    app.run(debug=True)
