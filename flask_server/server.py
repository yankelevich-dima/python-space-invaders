from app import app
import views  # NOQA

if __name__ == '__main__':
    app.run(port=8000, debug=True)
