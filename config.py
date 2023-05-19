#---------------------Librerias-----------------
import telebot as tebot
import threading
import Levenshtein
import win32com.client as win32
import pytz
from datetime import datetime, timedelta
import pythoncom
import time
import locale
import firebase_admin
from firebase_admin import credentials , firestore

#---------------------Chat bot-----------------
telegram_token = "6091780715:AAFLq5xI93hVpjduisiLH_uE4yDgv5nTgTc"

response = None

entrenamiento = {
    "saludo": {"hola", "buenos días", "hols", "hpla" "buenas tardes", "hpls", "buenas", "burnas", "hola como estas", "buenas noches", "hoola","halo", "jola", "chola", "shola", "hila", "hola!", "hola.", "hola?", "hola...", "hola!!", "h0la", "h@la", "ho1a", "hoIa", "h0l4", "hola!", "hola,", "hola:", "hola;", "hola)", "hola]", "hola}", "hola(", "hola[", "hola{", 'buens tardes', 'buenas tades', 'bunas tardes', 'buena tarde', 'buena tares', 'buenas tardas', 'buena tarda', 'buenas tardea', 'buena tard', 'buena tares',"buenas tardes",'nuenas tsrdea', 'buens tardea'},
    "despedida": {"fin", "finalizar", "salir", "gracias","fonslizar", "finalozar", "fom", "fim!",'Adiós', 'Chao', 'Hasta luego', 'Cerrar chat', 'Fin del chat', 'Me voy', 'Ya no', 'Es todo', 'Hasta pronto',           'Me despido', 'Terminar conversación', 'Fin de la conversación', 'Cerrar conversación', 'Terminé', 'Finalizar chat',           'Es hora de irme', 'Gracias', 'Hasta la próxima', 'Ya he acabado', 'Me retiro', 'Ha sido de gran ayuda',           'Ya tengo lo que necesito', 'Muchas gracias', 'Adiós, hasta pronto', 'Eso es todo', 'Ya terminé',           'No tengo más preguntas', 'Fin de la charla', 'Adiós, gracias', 'Es todo por ahora'},
    "pedir cita" : {"quiero cita" , "quiero agendar mi cita médica", "quiero agendar mi cita", "quiero agendar mi primera cita", "quiero agendar mi segunda cita","agendar cita","me gustaria programar una cita médica", "quiero agendar una cita","quiero agendar", "quiero una cita", "quierp una cita","quiero agendar mi primera cita","quierp agendar una cita", 'quiero sgendar una cita', 'quiero sggendar una cita', 'quiero agsendar una cita', 'quiero agendsr una cita', 'quiero agendar una cits', 'quiero sggendar una cits', 'quiero agsendar una cits', 'quiero agendar una sits', 'quiero agendar una csta', 'quiero agendar una ssta', 'quiero agendar una csts', 'quiero agendar una ssts', 'quiero agendar una ctta', 'quiero agendar una stta', 'quiero agendar una ctsa', 'quiero agendar una stsa', "quiero una cita",    "quiere una cita",    "quiero una cinta",    "quiero una cota",    "quiero una pita",    "quiero un cita",    "quiero un cita por favor",    "deseo una cita",    "agendar una cita",    "pedir una cita medica",           'Necesito ver al doctor.'},
    "cancelar cita" : {"quiero cancelar mi cita", "quiero cancelar","cancelar", "quiero cancelar una cita", "quierp cancelar mi cita","quiero cancelsr mi cits","quiero cancelat mu cita", "quirro cancelar una cita"},
    "mañana" : {"en la mañana", "mañana", "en mañana","en la marana", "la mañana" ,"en la manaña",  "en la mañama",  "en la mañaa", "por la mañana" , "en la mrañana",  "en la mñana",  "en la mnañana",  "en la mañaa",  "en la mañan",  "en la mañanna",  "en la mñanaa",  "en la mañama",  "en la mañanha",  "en la mañana ",  "en la mañana.",  "enla mañana",  "en lamañana",  "en lamñana",  "en la mnaana",  "en la ma;ana"},
    "tarde" : {"en la tarde",  "en la tardr","en tarde", "tarde",  "en la tsrde", "por la tarde" ,"la tarde" ,"en la tardes",  "rn la tasde",  "en la trde",  "en la tade",  "en la tadr",  "en la tardee",  "en la tarda",  "en la tadee",  "en la tarrde",  "en la tards",  "en la trdae",  "en la taerde",  "en la tadre",  "en la taardee",  "en la tarae",  "en la tard",  "en la tade."},
    "registro": {"ya me registre", 'Ya me registré antes', 'Me he registrado previamente', 'Ya tengo cuenta aquí', 'Ya tengo una cuenta', 'Me he registrado exitosamente', 'Ya completé el registro', 'Ya hice mi registro', 'Ya me he inscrito','Estoy registrado en línea', 'Ya estoy en el sistema', "ys me registre",  "ya ne registre",},
    "afirmacion" : {"di", "si", "ai", "so", "ao"},
    "negacion" : {"no", "np", "mo", "mp", "ño"}
}

#-----------------Declaración de variables---------------
users = {}
paciente_f = {}

last_active = {}
doc_dict = {}
todos_los_datos = {}

citas_AM = []
citas_PM = []

total_disponible_AM = []
total_disponible_PM = []

hora_disponible_AM = []
hora_disponible_PM = []

mes_cita = ""
hora_cita = ""
dia_cita = ""

#----------------Llamado a Outlook---------------
outlook = win32.Dispatch('Outlook.Application')
calendar = outlook.GetNamespace('MAPI').GetDefaultFolder(9)
event = outlook.CreateItem(1)  # 1 significa "olAppointmentItem" (evento)
#----------------Tiempo de cada cita---------------
# Duración del tiempo que desea verificar (en este caso, 1 hora)
duration = timedelta(hours=1)
bot = tebot.TeleBot(telegram_token)
#----------------Llamado a Firebase para leer datos---------------
cred = credentials.Certificate("jeje.json")
firebase_admin.initialize_app(cred)
DB = firestore.client()
doc_ref = DB.collection(u"pacientes")
#----------------Funciones del chatbot---------------

#----------------Clasificador de texto KNN---------------
def knn_clasificador(palabra_prueba, conjunto_entrenamiento):
    k = 1  # Número de vecinos más cercanos a considerar
    distancias = []  # Lista para almacenar las distancias entre la palabra de prueba y las palabras de entrenamiento
    for etiqueta, palabras_entrenamiento in conjunto_entrenamiento.items():
        for palabra_entrenamiento in palabras_entrenamiento:
            distancia = Levenshtein.distance(palabra_prueba, palabra_entrenamiento)
            distancias.append((distancia, etiqueta))  # Almacenar la distancia y la etiqueta correspondiente
    distancias = sorted(distancias)  # Ordenar las distancias de menor a mayor
    k_vecinos_cercanos = distancias[:k]  # Obtener los k vecinos más cercanos
    etiqueta_predicha = k_vecinos_cercanos[0][1]  # Etiqueta de la primera instancia más cercana
    distancia_minima = k_vecinos_cercanos[0][0]  # Distancia mínima entre la palabra de prueba y los vecinos cercanos
    # Calcular umbral para determinar si la palabra de prueba pertenece a alguna categoría
    if len(palabra_prueba) > 7:
        umbral = int(0.4 * len(palabra_prueba))
    else:
        umbral = int(0.5 * len(palabra_prueba))
    if distancia_minima > umbral:  # Si la distancia mínima supera el umbral, la palabra no pertenece a ninguna categoría
        etiqueta_predicha = "No pertenece a ninguna categoría"
    return etiqueta_predicha


#----------------Define la hora de finalización de cada cita---------------
def horario_cita(cita):
    primer_espacio = cita.find(" ")  # Encontrar el primer espacio en la cadena de la cita
    segundo_espacio = cita.find(" ", primer_espacio + 1)  # Encontrar el segundo espacio
    tercer_espacio = cita.find(" ", segundo_espacio + 1)  # Encontrar el tercer espacio
    cita_inicio = cita[primer_espacio + 1 : tercer_espacio]  # Extraer la parte de la cita que contiene la hora de inicio
    espacio_cita = cita_inicio.find(" ")  # Encontrar el espacio dentro de la parte de la cita que contiene la hora de inicio
    dos_puntos = cita_inicio.find(":")  # Encontrar los dos puntos que separan la hora y los minutos
    hora = cita_inicio[espacio_cita + 1 : dos_puntos]  # Extraer la hora de inicio de la cita
    # Calcular la hora de finalización de la cita según la hora de inicio
    if hora == "08":
        hora_fin = "09"
        s_list = list(cita_inicio)
        ultima_hora = cita_inicio.rfind(hora)
        s_list[ultima_hora : ultima_hora + 2] = hora_fin
        cita_fin = "".join(s_list)
    elif hora == "09":
        hora_fin = "10"
        s_list = list(cita_inicio)
        ultima_hora = cita_inicio.rfind(hora)
        s_list[ultima_hora : ultima_hora + 2] = hora_fin
        cita_fin = "".join(s_list)
    else:
        hora_fin = int(hora) + 1
        s_list = list(cita_inicio)
        ultima_hora = cita_inicio.rfind(str(hora))
        s_list[ultima_hora : ultima_hora + 2] = str(hora_fin)
        cita_fin = "".join(s_list)
    return cita_inicio, cita_fin


#----------------Detecta el mes actual---------------
def mes_actual(mes):
    mes_30 = 30  # Constante para representar el número de días en un mes con 30 días
    mes_31 = 31  # Constante para representar el número de días en un mes con 31 días
    mes_28 = 28  # Constante para representar el número de días en febrero (mes con 28 días o 29 en años bisiestos)

    if mes == 1 or mes == 3 or mes == 5 or mes == 7 or mes == 8 or mes == 10 or mes == 12:  
        return mes_31  # Si el mes es 1, 3, 5, 7, 8, 10 o 12, devuelve el número de días correspondiente a un mes con 31 días
    elif mes == 2:
        return mes_28  # Si el mes es 2, devuelve el número de días correspondiente a febrero
    else:
        return mes_30  # Para cualquier otro mes, devuelve el número de días correspondiente a un mes con 30 días


#----------------Encuentra fechas sin eventos agendados---------------
def eventos_libres():
    pythoncom.CoInitialize()
    # Obtener la hora actual en la zona horaria 'America/Bogota'
    hora = datetime.now(pytz.timezone('America/Bogota'))
    # Obtener la instancia de Outlook y el calendario predeterminado
    outlook = win32.Dispatch('Outlook.Application').GetNamespace('MAPI')
    calendario = outlook.GetDefaultFolder(9)
    # Obtener la fecha y hora actual
    hoy = datetime.now()
    hoy = hoy.strftime("%A %d/%m/%Y %H:%M %p")
    # Obtener el número de días en el mes actual
    dias_en_mes_actual = mes_actual(hora.month) #calendar.monthrange(hora.year, hora.month)[1]
    # Calcular el día inicial para cada tipo de día
    dia_inicial_viernes = hora.day + 3
    dia_inicial_sabado = hora.day + 2
    dia_inicial_dia_laboral = hora.day + 1
    tot_disp = []  # Lista para almacenar los horarios disponibles
    # Determinar el día de inicio según el día actual
    if "Friday" in str(hoy):
        if dia_inicial_viernes > dias_en_mes_actual:
            mes_siguiente = hora.month + 1
            dia_inicial = 1
            start_time = datetime(hora.year, mes_siguiente, dia_inicial, 8, 0, 0, tzinfo=pytz.timezone('America/Bogota'))
        else:
            start_time = datetime(hora.year, hora.month, dia_inicial_viernes, 8, 0, 0, tzinfo=pytz.timezone('America/Bogota'))
    elif "Saturday" in str(hoy):
        if dia_inicial_sabado > dias_en_mes_actual:
            mes_siguiente = hora.month + 1
            dia_inicial = 1
            start_time = datetime(hora.year, mes_siguiente, dia_inicial, 8, 0, 0, tzinfo=pytz.timezone('America/Bogota'))
        else:
            start_time = datetime(hora.year, hora.month, dia_inicial_sabado, 8, 0, 0, tzinfo=pytz.timezone('America/Bogota'))
    else:
        if dia_inicial_dia_laboral > dias_en_mes_actual:
            mes_siguiente = hora.month + 1
            dia_inicial = 1
            start_time = datetime(hora.year, mes_siguiente, dia_inicial, 8, 0, 0, tzinfo=pytz.timezone('America/Bogota'))
        else:
            start_time = datetime(hora.year, hora.month, dia_inicial_dia_laboral, 8, 0, 0, tzinfo=pytz.timezone('America/Bogota'))
    locale.setlocale(locale.LC_ALL, 'es_ES')
    duration = timedelta(minutes=30)  # Duración de cada evento (30 minutos)
    while len(tot_disp) < 60:  # Obtener 60 horarios disponibles
        end = start_time + duration
        # Crear filtro para consultar eventos dentro del rango de tiempo especificado
        filter = "[Start] >= '{0}' AND [End] <= '{1}'".format(start_time.strftime('%A %d/%m/%Y %H:%M'), end.strftime('%A %d/%m/%Y %H:%M'))
        # Restringir eventos según el filtro
        events = calendario.Items.Restrict(filter)
        if len(events) == 1:
            start_time += duration  # Si hay un evento, avanzar al siguiente intervalo de tiempo
        else:
            # Si no hay eventos, agregar la cita disponible a 'tot_disp'
            cita_disp = "{0}".format(start_time.strftime('%A %d/%m/%Y %H:%M'))
            tot_disp.append(cita_disp)
            start_time += duration  # Avanzar al siguiente intervalo de tiempo
        return tot_disp
#----------------Agenda la cita 1---------------
def agendar_evento_1(update, context,fecha_in, fecha_out, docu, correo_destino):
    # Conecta con la aplicación de Outlook
    pythoncom.CoInitialize()
    outlook = win32.Dispatch("Outlook.Application")
    # Crea una nueva cita
    appointment = outlook.CreateItem(1)  # 1 es el valor para citas
    # Configura los campos de la cita
    appointment.Subject = "Cita 1: valoración médica y diagnóstico preliminar {}".format(docu)
    appointment.Start = fecha_in
    appointment.End = fecha_out
    appointment.Location = "Laboratorio Baspi-Footlab"
    appointment.Body = "Hola, espero estés muy bien. \nTe quiero informar que tu cita ha sido agendada correctamente. \n\nRecuerda, si tienes alguna plantilla ortopedica, traela el día de la cita para realizar un estudio detallado.\n\n Que tengas buen día\n\n¡Te esperamos!"
    # Agrega el correo electrónico del destinatario
    appointment.RequiredAttendees = correo_destino
    appointment.ReminderMinutesBeforeStart = 60
    appointment.MeetingStatus = 1 
    appointment.Save()
    appointment.Send()

#----------------Agenda la cita 2---------------
def agendar_evento_2(update, context,fecha_in, fecha_out, docu, correo_destino):
    # Conecta con la aplicación de Outlook
    pythoncom.CoInitialize()
    outlook = win32.Dispatch("Outlook.Application")
    # Crea una nueva cita
    appointment = outlook.CreateItem(1)  # 1 es el valor para citas
    # Configura los campos de la cita
    appointment.Subject = "Cita 2: toma de datos biomecánicos y toma de molde 3D {}".format(docu)
    appointment.Start = fecha_in
    appointment.End = fecha_out
    appointment.Location = "Laboratorio Baspi-Footlab"
    appointment.Body = "Hola, espero estés muy bien. \nTe quiero informar que tu cita ha sido agendada correctamente. \n\nRecuerda, si tienes alguna plantilla ortopedica, traela el día de la cita para realizar un estudio detallado.\n\n Que tengas buen día\n\n¡Te esperamos!"
    # Agrega el correo electrónico del destinatario
    appointment.RequiredAttendees = correo_destino
    appointment.ReminderMinutesBeforeStart = 60
    appointment.MeetingStatus = 1 
    appointment.Save()
    appointment.Send()

#----------------Cancelación de citas---------------
def cancelar_evento(update, context, docu):
    pythoncom.CoInitialize()
    # Crear una instancia de la aplicación Outlook
    outlook = win32.Dispatch("Outlook.Application")
    # Crear una instancia del objeto de calendario
    appointments = outlook.GetNamespace("MAPI").GetDefaultFolder(9).Items.Restrict("[Subject]='Cita 1: valoración médica y diagnóstico preliminar {}' AND [Start] >= '{}' ".format(docu, datetime.now()))
    # Buscar la reunión por asunto
    if appointments.Count == 0:
    # No se encontró ninguna cita con el sujeto especificado
        appointments = outlook.GetNamespace("MAPI").GetDefaultFolder(9).Items.Restrict("[Subject]='Cita 2: toma de datos biomecánicos y toma de molde 3D {}' AND [Start] >= '{}' ".format(docu, datetime.now()))
        if appointments.Count == 0:
            return None
    event = appointments[0]
    # Rechazar la reunión
    event.MeetingStatus = 5  # 5 representa la constante de Canceled
    for recipient in event.Recipients:
        recipient.MeetingResponseStatus = 3  # 3 representa la constante de Declined

    event.Send()
    event.Delete()

#----------------Encuentra enventos agendados---------------
def evento_para_cancelar(update, context, docu):
    pythoncom.CoInitialize()
    outlook = win32.Dispatch("Outlook.Application")
    # Obtener una referencia al evento que deseas eliminar
    appointments = outlook.GetNamespace("MAPI").GetDefaultFolder(9).Items.Restrict("[Subject]='Cita 1: valoración médica y diagnóstico preliminar {}' AND [Start] >= '{}' ".format(docu, datetime.now()))

    if appointments.Count == 0:
        # No se encontró ninguna cita con el sujeto especificado
        appointments = outlook.GetNamespace("MAPI").GetDefaultFolder(9).Items.Restrict("[Subject]='Cita 2: toma de datos biomecánicos y toma de molde 3D {}' AND [Start] >= '{}' ".format(docu, datetime.now()))
        if appointments.Count == 0:
            return None
    event = appointments[0]
    start = event.Start
    sub = event.Subject
    fecha_cancelar = start.strftime("%A %d/%m/%Y %I:%M %p")
    return fecha_cancelar, sub

