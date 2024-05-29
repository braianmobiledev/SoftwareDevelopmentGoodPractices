from flask import Flask, request, jsonify
from validators.verificadores import Autenticador, Validador, Filtro_IP, Cache
from flask_cors import CORS
from clientes import app as app_clientes
from bson import ObjectId

app = Flask(__name__)
CORS(app)

# Esta función convierte ObjectId a str
def serializar_objectid(doc):
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = serializar_objectid(value)
    return doc

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

# Rutas para el CRUD de clientes

# Crear un cliente
@app.route('/clientes', methods=['POST'])
def crear_cliente():
    # Obtener los datos del cliente desde la solicitud
    datos_cliente = request.get_json()
    
    # Verificar si el usuario está autenticado
    if autenticador.procesar_solicitud(request.json):
        # Insertar los datos del cliente en la colección de MongoDB
        cliente_id = autenticador.coleccion.insert_one(datos_cliente).inserted_id
        return jsonify({"mensaje": "Cliente creado con éxito", "cliente_id": str(cliente_id)})
    else:
        return jsonify({"mensaje": "No autorizado para crear clientes"})

# Leer todos los clientes
@app.route('/clientes', methods=['GET'])
def obtener_clientes():
    # Verificar si el usuario está autenticado
    if autenticador.procesar_solicitud(request.json):
        # Obtener todos los clientes desde la colección de MongoDB
        clientes = list(autenticador.coleccion.find())
        # Serializar los ObjectId a cadenas de texto
        clientes_serializados = [serializar_objectid(cliente) for cliente in clientes]
        return jsonify(clientes_serializados)
    else:
        return jsonify({"mensaje": "No autorizado para ver clientes"})

# Leer un cliente por ID
@app.route('/clientes/<cliente_id>', methods=['GET'])
def obtener_cliente_por_id(cliente_id):
    # Verificar si el usuario está autenticado
    if autenticador.procesar_solicitud(request.json):
        # Obtener un cliente por ID desde la colección de MongoDB
        cliente = autenticador.coleccion.find_one({"_id": cliente_id})
        if cliente:
            # Serializar los ObjectId a cadenas de texto
            clientes_serializados = serializar_objectid(cliente)
            return jsonify(cliente)
        else:
            return jsonify({"mensaje": "Cliente no encontrado"}, 404)
    else:
        return jsonify({"mensaje": "No autorizado para ver clientes"})

# Actualizar un cliente por ID
@app.route('/clientes/<cliente_id>', methods=['PUT'])
def actualizar_cliente(cliente_id):
    # Verificar si el usuario está autenticado
    if autenticador.procesar_solicitud(request.json):
        # Obtener los nuevos datos del cliente desde la solicitud
        nuevos_datos = request.get_json()
        
        # Actualizar el cliente en la colección de MongoDB
        resultado = autenticador.coleccion.update_one({"_id": cliente_id}, {"$set": nuevos_datos})
        if resultado.modified_count > 0:
            return jsonify({"mensaje": "Cliente actualizado con éxito"})
        else:
            return jsonify({"mensaje": "Cliente no encontrado o no se realizaron cambios"}, 404)
    else:
        return jsonify({"mensaje": "No autorizado para actualizar clientes"})

# Borrar un cliente por ID
@app.route('/clientes/<cliente_id>', methods=['DELETE'])
def borrar_cliente(cliente_id):
    # Verificar si el usuario está autenticado
    if autenticador.procesar_solicitud(request.json):
        # Eliminar el cliente de la colección de MongoDB
        resultado = autenticador.coleccion.delete_one({"_id": cliente_id})
        if resultado.deleted_count > 0:
            return jsonify({"mensaje": "Cliente eliminado con éxito"})
        else:
            return jsonify({"mensaje": "Cliente no encontrado o no se eliminó"}, 404)
    else:
        return jsonify({"mensaje": "No autorizado para eliminar clientes"})

if __name__ == '__main__':
    app.run(debug=True)