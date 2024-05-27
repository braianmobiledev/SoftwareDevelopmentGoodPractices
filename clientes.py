from flask import Flask, request, jsonify
from pymongo import MongoClient
from verificadores import Autenticador

app = Flask(__name__)

# Datos para la conexión a MongoDB
url_conexion = "mongodb+srv://braian74:#Braian0410@sdgoodpractices.ro7urth.mongodb.net/?retryWrites=true&w=majority&appName=SDGoodPractices"
base_de_datos = "Order"
coleccion = "Clientes"

# Crear un objeto Autenticador con los datos de conexión
autenticador = Autenticador(url_conexion, base_de_datos, coleccion)

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
        return jsonify(clientes)
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
