from flask import Flask, request, jsonify
from flask_cors import CORS

# from clientes import app as app_clientes
from bson import ObjectId
from abc import ABC, abstractmethod
from flask import Flask, request
import pymongo
import re
from cachetools import TTLCache

app = Flask(__name__)

# Esta función convierte ObjectId a str
def serializar_objectid(doc):
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = serializar_objectid(value)
    return doc

class Verificador(ABC):
    def establecer_siguiente(self, siguiente):
        self.siguiente_verificador = siguiente
        self.error = None

    @abstractmethod
    def procesar_solicitud(self, datos_solicitud):
        pass

class Autenticador(Verificador):
    def __init__(self, url_conexion, base_de_datos, coleccion):
        self.client = pymongo.MongoClient(url_conexion)
        self.db = self.client[base_de_datos]
        self.coleccion = self.db[coleccion]

    def procesar_solicitud(self, datos_solicitud):
        usuario = datos_solicitud.get("usuario")
        contraseña = datos_solicitud.get("contraseña")

        usuario_encontrado = self.coleccion.find_one({"usuario": usuario, "contraseña": contraseña})
        if usuario_encontrado:
            return True
        else:
            return False

class Validador(Verificador):
    def procesar_solicitud(self, datos_solicitud):
        # Realiza la validación adicional aquí (personaliza según tus necesidades)
        datos_sanitizados = self.sanear_datos(datos_solicitud)
        
        # Verificar si los datos son nulos (indicativo de una validación fallida)
        if datos_sanitizados is None:
            return False

        # Continúa con la validación utilizando los datos sanitizados
        if self.siguiente_verificador:
            return self.siguiente_verificador.procesar_solicitud(datos_sanitizados)
        else:
            return True

    def sanear_datos(self, datos_solicitud):
        usuario = datos_solicitud.get("usuario")
        if self.es_direccion_de_correo(usuario):
            return datos_solicitud
        else:
            return None  # Si no es una dirección de correo válida, retorna None

    def es_direccion_de_correo(self, usuario):
        expresion_regular = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(expresion_regular, usuario) is not None

class Filtro_IP(Verificador):
    def __init__(self):
        self.intentos_por_ip = {}

    def procesar_solicitud(self, datos_solicitud):
        direccion_ip = request.remote_addr
        if direccion_ip in self.intentos_por_ip:
            intentos = self.intentos_por_ip[direccion_ip]
            if intentos >= 3:
                return False
            self.intentos_por_ip[direccion_ip] += 1
        else:
            self.intentos_por_ip[direccion_ip] = 1
        
        if self.siguiente_verificador:
            return self.siguiente_verificador.procesar_solicitud(datos_solicitud)
        else:
            return True

class Cache(Verificador):
    def __init__(self):
        # Crea una caché con un tamaño máximo de 100 elementos y un tiempo de vida de 60 segundos para cada elemento
        self.cache = TTLCache(maxsize=100, ttl=60)

    def obtener(self, clave):
        # Intenta obtener un valor de la caché
        return self.cache.get(clave)

    def almacenar(self, clave, valor):
        # Almacena un valor en la caché
        self.cache[clave] = valor

    def esta_en_cache(self, clave):
        # Verifica si una clave está en la caché
        return clave in self.cache

    def procesar_solicitud(self, datos_solicitud):
        # Verifica si la solicitud está en caché
        clave_cache = str(datos_solicitud)  # Clave de caché basada en los datos de solicitud
        if self.esta_en_cache(clave_cache):
            # Si está en caché, retorna la respuesta almacenada en caché
            respuesta_en_cache = self.obtener(clave_cache)
            return respuesta_en_cache

        if self.siguiente_verificador:
            # Si hay un siguiente verificador, pasa la solicitud a través de él
            respuesta = self.siguiente_verificador.procesar_solicitud(datos_solicitud)

            # Almacena la respuesta en caché
            self.almacenar(clave_cache, respuesta)

            return respuesta

        # Si no hay un siguiente verificador, simplemente almacena en caché la respuesta vacía
        respuesta_vacia = {"mensaje": "No hay verificadores posteriores, almacenando respuesta vacía en caché"}
        self.almacenar(clave_cache, respuesta_vacia)
        return respuesta_vacia


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
    
@app.route('/', methods=['GET'])
def main():
    return jsonify({"mesage": "Welcome to sample API"})



# Leer todos los clientes
@app.route('/clientes', methods=['GET'])
def obtener_clientes():
    # Verificar si el usuario está autenticado
    if autenticador.procesar_solicitud(request.json):
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