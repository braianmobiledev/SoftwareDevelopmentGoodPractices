from flask import Flask, request, jsonify
from verificadores import Autenticador, Validador, Filtro_IP, Cache
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


# Datos para la conexión a MongoDB
url_conexion = "mongodb+srv://braian74:#Braian0410@sdgoodpractices.ro7urth.mongodb.net/?retryWrites=true&w=majority&appName=SDGoodPractices"
base_de_datos = "Order"
coleccion = "Clientes"

# Crear objetos Autenticador, Validador, Filtro_IP y Cache con los datos de conexión
validador = Validador()
autenticador = Autenticador(url_conexion, base_de_datos, coleccion)
filtro_ip = Filtro_IP()
cache = Cache()

# Establecer las relaciones
validador.establecer_siguiente(filtro_ip)
filtro_ip.establecer_siguiente(cache)
cache.establecer_siguiente(autenticador)

# Ruta de autenticación en Flask
@app.route('/autenticar', methods=['POST'])
def autenticar():
    try:
        datos_solicitud = request.get_json()
        
        if not validador.procesar_solicitud(datos_solicitud):
            # Return a 400 Bad Request status for data validation failure
            return jsonify({"mensaje": "Validación de datos fallida"}), 400
        
        if not filtro_ip.procesar_solicitud(datos_solicitud):
            # Return a 429 Too Many Requests status for too many attempts from the same IP
            return jsonify({"mensaje": "Demasiados intentos desde la misma IP"}), 429

        if not cache.procesar_solicitud(datos_solicitud):
            # Return a 500 Internal Server Error status for cache verification failure
            return jsonify({"mensaje": "Fallo al verificar en la caché"}), 500

        if not autenticador.procesar_solicitud(datos_solicitud):
            # Return a 401 Unauthorized status for authentication failure
            return jsonify({"mensaje": "Autenticación fallida"}), 401

        usuario = datos_solicitud.get("usuario")
        contraseña = datos_solicitud.get("contraseña")

        usuario_encontrado = autenticador.coleccion.find_one({"usuario": usuario, "contraseña": contraseña})

        if usuario_encontrado:
            if usuario_encontrado["rol"] == "admin":
                return jsonify({"mensaje": "Autenticación exitosa como administrador"})
            else:
                return jsonify({"mensaje": "Autenticación exitosa como usuario estándar"})

        # Return a 401 Unauthorized status if the user is not found in the database
        return jsonify({"mensaje": "Usuario no encontrado in the base de datos"}), 401

    except Exception as e:
        # Handle and log the exception as needed
        return jsonify({"mensaje": "Error interno del servidor"}), 500

if __name__ == '__main__':
    app.run(debug=True)