from website import create_app
from website.views import views  # Import Blueprint

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)