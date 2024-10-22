from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import time
from tkinterweb import HtmlFrame

#Clase para gestionar el navegador y la automatización con Selenium
class BrowserManager:
    def __init__(self, logger):
        #Configuración de opciones para Chrome
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        #Inicializa el driver de Chrome
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        self.logger = logger

    #Método para rechazar cookies en la página
    def rechazar_cookies(self):
        try:
            boton_rechazar = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'onetrust-reject-all-handler'))
            )
            boton_rechazar.click()
            self.logger("Cookies rechazadas.")
        except Exception as e:
            self.logger("Error al rechazar las cookies.")

    #Método para hacer clic en posiciones aleatorias de la página
    def hacer_clicks_random(self):
        for _ in range(4):
            x = random.randint(100, 1820)  #Coordenada X aleatoria
            y = random.randint(100, 900)   #Coordenada Y aleatoria
            element = self.driver.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);", x, y)
            if element is not None:
                element.click()
                self.logger(f"Clic en posición: ({x}, {y})")
            time.sleep(3)

    #Método para cargar más anuncios desde la página
    def cargar_mas_anuncios(self):
        try:
            boton_mostrar_mas = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//walla-button[@id='btn-load-more']"))
            )

            while True:
                is_displayed = boton_mostrar_mas.is_displayed()

                if is_displayed:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_mostrar_mas)
                    time.sleep(1)
                    boton_mostrar_mas.click()
                    self.logger("Cargando más anuncios...")
                    time.sleep(5)
                    break
                else:
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    self.logger("Haciendo scroll para buscar el botón 'Mostrar más anuncios'...")
                    time.sleep(2)
        except Exception as e:
            self.logger("No hay más anuncios para cargar o se ha producido un error.")

    #Método para hacer scroll infinito en la página
    def scroll_infinito(self):
        try:
            previous_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.logger("Haciendo scroll hacia abajo...")
                time.sleep(3)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == previous_height:
                    self.logger("No hay más anuncios para cargar.")
                    break
                previous_height = new_height
        except Exception as e:
            self.logger(f"Ocurrió un error inesperado en el scroll.")
    
    #Método para cerrar el navegador
    def cerrar(self):
        self.driver.quit()

#Clase para gestionar el envío de correos electrónicos
class EmailManager:
    def __init__(self, remitente, contrasena, logger):
        self.remitente = remitente
        self.contrasena = contrasena
        self.logger = logger
        
    #Método para enviar un correo electrónico
    def enviar_correo(self, destinatario, asunto, mensaje):
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(self.remitente, self.contrasena)

        msg = MIMEMultipart()
        msg['From'] = self.remitente
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(mensaje, 'plain'))

        servidor.send_message(msg)
        servidor.quit()
        self.logger(f"Correo enviado a {destinatario} con el asunto '{asunto}'.")

#Clase para gestionar la obtención y procesamiento de anuncios
class AdsScraper:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    #Método para obtener anuncios de la página
    def obtener_anuncios(self):
        html_content = self.driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        anuncios = soup.find_all('a', class_='ItemCardList__item')
        return anuncios

    #Método para procesar los anuncios obtenidos
    def procesar_anuncios(self, anuncios, anuncios_guardados):
        nuevos = []
        for anuncio in anuncios:
            try:
                titulo = anuncio.find('p', class_='ItemCard__title')
                link = anuncio['href']
                titulo_texto = titulo.text.strip() if titulo else "Título no disponible"

                if titulo_texto not in anuncios_guardados:
                    anuncios_guardados[titulo_texto] = link
                    nuevos.append((titulo_texto, link))
            except Exception as ex:
                self.logger(f"Error al procesar un anuncio: {ex}")
        return nuevos

# Clase para gestionar la lectura y escritura de archivos CSV
class CSVManager:
    def __init__(self, filename):
        self.filename = filename

    # Método para cargar anuncios desde un archivo CSV
    def cargar_anuncios_csv(self):
        directorio = os.path.dirname(self.filename)
        
        if not os.path.exists(directorio):
            os.makedirs(directorio)
            print(f"Directorio creado: {directorio}")
        
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                print(f"Archivo creado: {self.filename}")
        
        if os.path.exists(self.filename):
            with open(self.filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                return {row[0]: row[1] for row in reader}
        return {}

    #Método para guardar nuevos anuncios en un archivo CSV
    def guardar_anuncios_csv(self, nuevos_anuncios):
        with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for titulo, link in nuevos_anuncios:
                writer.writerow([titulo, link])

#Clase para gestionar la interfaz de usuario con Tkinter
class UserInterface:
    def __init__(self, scraper):
        self.scraper = scraper
        self.root = tk.Tk()  #Crear ventana principal
        self.root.title("Wallapop Scraper Panel")  #Título de la ventana
        self.root.geometry("600x400")  #Tamaño de la ventana

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.start_button = tk.Button(self.frame, text="Iniciar Rastreo", command=self.iniciar_scraping)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.terminal = scrolledtext.ScrolledText(self.frame, height=15, width=80)  #Área de texto para mostrar logs
        self.terminal.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.scraping = False

    #Método para iniciar el proceso de scraping
    def iniciar_scraping(self):
        self.start_button.config(state=tk.DISABLED)  #Deshabilitar el botón mientras se está rastreando
        self.scraping = True

        self.scraping_thread = Thread(target=self.run_scraping)  #Ejecutar el scraping en un hilo separado
        self.scraping_thread.start()

    #Método que ejecuta el scraping
    def run_scraping(self):
        self.scraper.iniciar_proceso(self.scraper.urls[0])  #Iniciar proceso con la primera URL
        while self.scraping:
            self.scraper.procesar_urls()  #Procesar URLs
            self.log_terminal("Esperando 30 segundos para el siguiente rastreo...")  #Log en la interfaz
            time.sleep(30)

    #Método para registrar mensajes en la interfaz
    def log_terminal(self, mensaje):
        self.terminal.insert(tk.END, mensaje + '\n')  #Insertar mensaje en el área de texto
        self.terminal.see(tk.END)  #Hacer scroll hacia abajo

#Clase principal del scraper de Wallapop
class WallapopScraper:
    def __init__(self, urls, correo_destinatario, logger):
        self.browser = BrowserManager(logger)  #Instancia del gestor del navegador
        self.email = EmailManager("emaildelremitente@gmail.com", "contraseñadeaplicacion", logger)  #Instancia del gestor de emails
        self.anuncio_manager = AdsScraper(self.browser.driver, logger)  #Instancia del gestor de anuncios
        self.csv_manager = CSVManager('data/anuncios_wallapop.csv')  #Instancia del gestor de CSV
        self.anuncios_guardados = self.csv_manager.cargar_anuncios_csv()  #Cargar anuncios guardados
        self.urls = urls  #URLs a rastrear
        self.correo_destinatario = correo_destinatario  #Destinatario del correo
        self.logger = logger  #Función para loguear mensajes

    #Método para iniciar el proceso de scraping en una URL específica
    def iniciar_proceso(self, url):
        self.logger(f"Abriendo la página: {url}")  #Log del proceso
        self.browser.driver.get(url)  #Abrir la URL
        WebDriverWait(self.browser.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'onetrust-banner-sdk'))  #Esperar que aparezca el banner de cookies
        )
        self.browser.rechazar_cookies()  #Rechazar cookies
        time.sleep(5)
        self.browser.hacer_clicks_random()  #Hacer clics aleatorios
        time.sleep(10)

    #Método para procesar cada URL en la lista
    def procesar_urls(self):
        for url in self.urls:
            self.logger(f"Procesando URL: {url}")  #Log de la URL
            self.browser.driver.get(url)  #Abrir la URL
            self.browser.cargar_mas_anuncios()  #Cargar más anuncios
            self.browser.scroll_infinito()  #Hacer scroll infinito

            nuevos_anuncios = self.anuncio_manager.obtener_anuncios()  #Obtener anuncios
            nuevos = self.anuncio_manager.procesar_anuncios(nuevos_anuncios, self.anuncios_guardados)  #Procesar anuncios nuevos

            if nuevos:
                self.logger("Nuevos anuncios encontrados:")
                for nuevo in nuevos:
                    self.logger(f'Título: {nuevo[0]} - Enlace: {nuevo[1]}')  #Log de nuevos anuncios
                    self.email.enviar_correo(self.correo_destinatario, f'Nuevos anuncios en Wallapop: {nuevo[0]}', nuevo[1])  #Enviar correo
                self.csv_manager.guardar_anuncios_csv(nuevos)  #Guardar nuevos anuncios en CSV
            else:
                self.logger("No hay nuevos anuncios.")
            time.sleep(10)  #Esperar antes de la siguiente iteración

# Lista de URLs a rastrear
urls = [
    # IRL de búsqueda ejemplo:
    #'https://es.wallapop.com/app/search?filters_source=search_box&keywords=palabrasdebusqueda&latitude=41.387917&longitude=2.1699187&distance=200000',
]

#Función para registrar mensajes en la interfaz de usuario
def log_message(mensaje):
    ui.log_terminal(mensaje)

#Inicializar el scraper y la interfaz de usuario
scraper = WallapopScraper(urls, "emaildeldestinatario@gmail.com", log_message)
ui = UserInterface(scraper)
ui.root.mainloop()  #Iniciar la interfaz gráfica
