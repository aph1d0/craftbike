from serwis_crm import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
