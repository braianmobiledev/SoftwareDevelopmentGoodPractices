from abc import ABC, abstractmethod
from flask import Flask, request
import pymongo
import re
from cachetools import TTLCache

app = Flask(__name__)

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
