from app import app
import os

if __name__ == "__main__":
    port = 5000
    host = "127.0.0.1"
    print(f"\n * Server berjalan di: http://{host}:{port}/")
    app.run(debug=False, host=host, port=port) 