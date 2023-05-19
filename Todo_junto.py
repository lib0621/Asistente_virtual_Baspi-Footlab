from config import *
#función lectura constante Firebase
def read_data():
    tiempo_ultima_lectura = time.time()  # Variable para almacenar el tiempo de la última lectura
    espera_entre_lecturas = 600  # 10 minutos (en segundos)
    while True:
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - tiempo_ultima_lectura
        #Tiempo de espera para lectura de datos
        if tiempo_transcurrido >= espera_entre_lecturas:
            #Lectura de datos
            doc_ref = DB.collection(u"pacientes")
            docs = doc_ref.get()
            #Guardar los datos en todos_los_tados
            for doc in docs:
                todos_los_datos[doc.id] = doc.to_dict()
            tiempo_ultima_lectura = tiempo_actual
        for cedula, paciente in todos_los_datos.items():
            #si la cedula ingresada esta en paciente_f y hay un acambio en los datos se envían los siguientes mensajes
            if cedula in paciente_f:
                if paciente["cita_uno_avisar"] != paciente_f[cedula]["cita_uno_avisar"]:
                    response = "Hola, vi que asististe a la primera cita de valoración médica, si deseas agendar la segunda cita  para la toma de datos biomecanicos y toma de molde 3d, házmelo saber"
                    bot.send_message(paciente_f[cedula]["chat_id"], response )
                    print(paciente_f)
                    print(f"La fecha del paciente con cedula {cedula} ha cambiado")
                    paciente_f[cedula]['cita_uno_avisar'] = todos_los_datos[cedula]['cita_uno_avisar'] 
                elif paciente["cita_dos_avisar"] != paciente_f[cedula]["cita_dos_avisar"]:
                    response = "Hola, vi que asististe a la segunda cita de datos biomecanicos y toma de molde 3d, la plantilla personalizada se demorará al rededor de 20 días hábiles para que puedas recogerla"
                    bot.send_message(paciente_f[cedula]["chat_id"], response )
                    print(paciente_f)
                    print(f"La fecha del paciente con cedula {cedula} ha cambiado")
                    paciente_f[cedula]['cita_dos_avisar'] = todos_los_datos[cedula]['cita_dos_avisar'] 
                elif paciente["plantilla"] != paciente_f[cedula]["plantilla"]:
                    response = "Hola, tu plantilla ya está lista para que la recojas, te esperamos lo más pronto posible para que continues con el tratamiento."
                    bot.send_message(paciente_f[cedula]["chat_id"], response )
                    print(paciente_f)
                    print(f"La fecha del paciente con cedula {cedula} ha cambiado")
                    programar_mensaje_plantila(paciente_f[cedula]["chat_id"], datetime.now())
                    paciente_f[cedula]['plantilla'] = todos_los_datos[cedula]['plantilla'] 
            else:
                print(f"No se encontró información del paciente con cedula {cedula} en el diccionario paciente_f")
        time.sleep(1)

#función Usuario inactivo
def check_inactive_users():
    while True:
        #Lectura de datos
        doc_ref = DB.collection(u"pacientes")
        time.sleep(200)
        docs = doc_ref.get()
        for doc in docs:
            todos_los_datos[doc.id] = doc.to_dict()   
        now = time.time()
        try:
            for chat_id in last_active.keys():
                # Calcula la cantidad de tiempo que ha pasado desde la última interacción
                elapsed_time = now - last_active[chat_id]
                print(elapsed_time)

                # Si han pasado más de 5 minutos, reinicia el flujo de la conversación para ese usuario
                if elapsed_time >= 300:
                    del users[chat_id]
                    del last_active[chat_id]
                    response = "El tiempo de espera se ha agotado, si te puedo ayudar en algo dejamelo saber"
                    bot.send_message(chat_id, response )
                    bot.clear_step_handler_by_chat_id(chat_id)
        except:
            print("jeje")

#Respuesta a cualquier texto
@bot.message_handler(content_types = ["text", "photo"])

# Función de iniciar chat
def bot_saludo(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    #Se inicializa cualquier conversación previa con ese chat ID
    if chat_id not in users:
        print("Chat ID no encontrado ")
    else:
        del users[chat_id]   
    decision = knn_clasificador(palabra, entrenamiento)  # Lectura de palabra escrita po el usuario
    if chat_id not in users:
        # Si el usuario no existe, se crea un nuevo objeto para almacenar su información
        users[chat_id] = {"documento_agendamiento": None}
        users[chat_id] = {"documento_cancelar": None}
    #Lectura de datos
    doc_ref = DB.collection(u"pacientes")
    docs = doc_ref.stream()
    for doc in docs:
        doc_dict[doc.id] = doc.to_dict()
    #Se verifica la intención del usuario
    if decision == "saludo" or palabra == "/start":
        response =  "Hola, bienvenido a Footlab ¿En qué podemos ayudarte?"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, bot_citas)
    elif decision == "pedir cita":
        response = "Claro, si ya te registraste y adjuntaste tu documentación o ya asististe a la primera cita (valoración médica), escribe tu número de cédula, por favor enviarlo sin letras, ni espacios, por otro lado, si vas a realizar el registro, cuéntanos cuando lo hayas realizado para continuar con el agendamiento de la primera cita.\nRecuerda que para el agendamiento de citas se requiere lo siguiente: \n1. Tu registro previamente en la página web, puedes acceder desde el siguiente link: https://laboratoriobaspifootlab.tech/TESIS/templatemo/Crearcuenta.html \n2. Para el agendamiento de cita adjuntar los siguientes documentos en PDF: Cédula y Antecedentes clínicos (si aplica)."
        bot.send_message(palabras.chat.id, response)
        bot.register_next_step_handler(palabras, usuario_registrado)
    elif decision == "cancelar cita": 
        response = "Claro que sí, para la cancelación de citas se requiere tu número de documento, por favor enviarlo sin letras, ni espacios."
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, documentacion_C)
    elif decision == "registro":
        response = "Perfecto, me podrías escribir número de documento, por favor enviarlo sin letras, ni espacios."
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, documentacion_A)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "Perdón, no entiendo que me quieres decir ¿Podrías volver a escribirlo?"
        bot.send_message(palabras.chat.id, response)

#función de porimera petición
def bot_citas(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if decision == "pedir cita":
        response = "Claro, si ya te registraste y adjuntaste tu documentación o ya asististe a la primera cita (valoración médica), escribe tu número de cédula, por favor enviarlo sin letras, ni espacios, por otro lado, si vas a realizar el registro, cuéntanos cuando lo hayas realizado para continuar con el agendamiento de la primera cita.\nRecuerda que para el agendamiento de citas se requiere lo siguiente: \n1. Tu registro previamente en la página web, puedes acceder desde el siguiente link: https://laboratoriobaspifootlab.tech/TESIS/templatemo/Crearcuenta.html \n2. Para el agendamiento de cita adjuntar los siguientes documentos en PDF: Cédula y Antecedentes clínicos (si aplica)."
        bot.send_message(palabras.chat.id, response)
        bot.register_next_step_handler(palabras, usuario_registrado)
    elif decision == "saludo":
        response = "Hola, bienvenido a Footlab ¿En qué podemos ayudarte?"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, bot_citas)
    elif decision == "cancelar cita": 
        response = "Claro que sí, para la cancelación de citas se requiere tu número de documento, por favor enviarlo sin letras, ni espacios."
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, documentacion_C)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "Perdón, no entiendo que me quieres decir ¿Podrías volver a escribirlo?"
        bot.send_message(palabras.chat.id, response)
        bot.register_next_step_handler(palabras, bot_citas)

#función de lectura de documento 
def usuario_registrado(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if palabra.isdigit():
        users[chat_id]["documento_agendamiento"] = palabra
        response = "Me puedes confirmar si tu documento es: " + users[chat_id]["documento_agendamiento"]
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confrima_doc_A)
    elif decision ==  "registro":
        response = "Perfecto, me podrías escribir número de documento, por favor enviarlo sin letras, ni espacios."
        bot.send_message(palabras.chat.id, response)
        bot.register_next_step_handler(palabras, documentacion_A)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "Perdón, no entiendo que me quieres decir ¿Podrías volver a escribirlo?"
        bot.send_message(palabras.chat.id, response)
        bot.register_next_step_handler(palabras, usuario_registrado)

#función de confirmación de documento 
def documentacion_A(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)# Lectura de palabra escrita po el usuario
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)
    #Se verifica la intención del usuario
    if palabra.isdigit():
        users[chat_id]["documento_agendamiento"] = palabra
        response = "Me puedes confirmar si tu documento es: " + users[chat_id]["documento_agendamiento"]
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confrima_doc_A)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "No entendi el documento ingresado ¿Podrías volver a escribirlo?A"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, documentacion_A)
 
#función de lectura de documento 
def documentacion_C(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if palabra.isdigit():
        users[chat_id]["documento_cancelar"] = palabra
        response = "Me puedes confirmar si tu documento es: " + users[chat_id]["documento_cancelar"]
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confrima_doc_C)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "No entendi el documento ingresado ¿Podrías volver a escribirlo?C"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, documentacion_C)

#función de documento correcto o incorrecto 
def confrima_doc_A(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)# Lectura de palabra escrita po el usuario
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)
    #Lectura de datos
    doc_ref = DB.collection(u"pacientes")
    docs = doc_ref.stream()
    #Se verifica la intención del usuario
    if decision == "afirmacion":
        for doc in docs:
            doc_dict[doc.id] = doc.to_dict()
        if users[chat_id]["documento_agendamiento"] in doc_dict:
            users[chat_id]["email"] = doc_dict[users[chat_id]["documento_agendamiento"]]["email"] 
            users[chat_id]["email_asteriscos"] = users[chat_id]["email"][:2] + "****" + users[chat_id]["email"][6:]
            response = "Perfecto, ¿Podría escribir su email completanto los asteriscos ? {}".format(users[chat_id]["email_asteriscos"])
            bot.send_message(palabras.chat.id, response )
            bot.register_next_step_handler(palabras, confirmar_email_A )
        else:
            del users[chat_id]
            del last_active[chat_id]
            response = "No encontramos ningún paciente con esa identificación, por favor regístrate en https://laboratoriobaspifootlab.tech/TESIS/templatemo/Crearcuenta.html e infórmanos cuando lo hagas" 
            bot.send_message(palabras.chat.id, response )
    elif decision == "negacion":
        response = "¿Me la podrias volver a escribir?"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, documentacion_A)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "Lo siento, no entendí lo que me quisiste decir"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confrima_doc_A)

#función de confirmación de documento 
def confrima_doc_C(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Lectura de datos
    doc_ref = DB.collection(u"pacientes")
    docs = doc_ref.stream()
    #Se verifica la intención del usuario
    if decision == "afirmacion":
        for doc in docs:
            doc_dict[doc.id] = doc.to_dict()
        if users[chat_id]["documento_cancelar"] in doc_dict:
            users[chat_id]["email"] = doc_dict[users[chat_id]["documento_cancelar"]]["email"] 
            users[chat_id]["email_asteriscos"] = users[chat_id]["email"][:2] + "****" + users[chat_id]["email"][6:]
            response = "Perfecto ¿Podría escribir su email completanto los asteriscos? {}".format(users[chat_id]["email_asteriscos"])
            bot.send_message(palabras.chat.id, response )
            bot.register_next_step_handler(palabras, confirmar_email_C )
        else:
            del users[chat_id]
            del last_active[chat_id]
            response = "No encontramos ningún paciente con esa identificación, por favor regístrate en https://laboratoriobaspifootlab.tech/TESIS/templatemo/Crearcuenta.html e infórmanos cuando lo hagas" 
            bot.send_message(palabras.chat.id, response )
    elif decision == "negacion":
        response = "¿Me la podrias volver a escribir?"
        bot.send_message(palabras.chat.id, response ) 
        bot.register_next_step_handler(palabras, documentacion_C)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "Lo siento, no entendí lo que me quisiste decir"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confrima_doc_C)

#función de confirmación de email
def confirmar_email_C(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if palabra == users[chat_id]["email"]:
        evento_cancelar = evento_para_cancelar(palabras ,None, users[chat_id]["documento_cancelar"] )
        if evento_cancelar == None:
            del users[chat_id]
            del last_active[chat_id]
            response = "No hay citas agendadas con esa identificación"
            bot.send_message(palabras.chat.id, response )
        else:
            response = "¿Esta es la cita que quieres cancelar? {}".format(evento_cancelar)
            bot.send_message(palabras.chat.id, response )
            bot.register_next_step_handler(palabras, confirmar_cita_c)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else:
        response = "El email ingresado no corresponde con el registrado, por favor escribalo otra vez"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confirmar_email_C)

#función de confirmación de cita a cancelar
def confirmar_cita_c(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if decision == "afirmacion":
        evento_cancelar , users[chat_id]["subject"] = evento_para_cancelar(palabras ,None, users[chat_id]["documento_cancelar"] )
        if "Cita 1" in users[chat_id]["subject"]:
            cancelar_evento(palabra, None, users[chat_id]["documento_cancelar"])
            documento_agendamiento = doc_ref.document(users[chat_id]["documento_cancelar"])
            documento_agendamiento.update({"fecha_uno": ""})
        if "Cita 2" in users[chat_id]["subject"]:
            cancelar_evento(palabra, None, users[chat_id]["documento_cancelar"])
            documento_agendamiento = doc_ref.document(users[chat_id]["documento_cancelar"])
            documento_agendamiento.update({"fecha_dos": ""})
        bot.send_message(palabras.chat.id, "La cita con la identificación {} ha sido cancelada, si deseas reagendar házmelo saber".format(users[chat_id]["documento_cancelar"]) )
    elif decision == "negacion":
        del users[chat_id]
        del last_active[chat_id]
        response = "Lo siento no tenemos más citas agendadas con este documento"
        bot.send_message(palabras.chat.id, response )
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else: 
        response = "Lo siento, no entendí lo que me quisiste decir"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confirmar_cita_c)

#función de confirmación de documento 
def confirmar_email_A(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if palabra == users[chat_id]["email"]:
        if doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"] == "":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "cita_uno_agendar": "1","plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            response = "¿Prefieres horario de la mañana o de la tarde?"
            bot.send_message(palabras.chat.id, response )
            bot.register_next_step_handler(palabras, bot_fecha )
        elif doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"]  == "INGRESADO":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id,"cita_uno_agendar": "2", "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            response = "¿Prefieres horario de la mañana o de la tarde?"
            bot.send_message(palabras.chat.id, response )
            bot.register_next_step_handler(palabras,  bot_fecha)
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else:
        response = "El email ingresado no corresponde con el registrado, por favor escribalo otra vez"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, confirmar_email_A)

# Función muestra fechas disponibles 
def bot_fecha(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    global citas_AM
    global citas_PM
    citas_AM = []
    citas_PM = []
    citas = eventos_libres()
    for i in citas:
        if "00:00" in i:
            continue
        elif "18:00" in i:
            continue
        elif "19:00" in i:
            continue
        elif "20:00" in i:
            continue
        elif "21:00" in i:
            continue
        elif "22:00" in i:
            continue
        elif "23:00" in i:
            continue
        elif "8:00" in i:
            citas_AM.append(i) 
        elif "9:00" in i:
            citas_AM.append(i) 
        elif "10:00" in i:
            citas_AM.append(i) 
        elif "11:00" in i:
            citas_AM.append(i) 
        elif "12:00" in i:
            citas_PM.append(i) 
        elif "14:00" in i:
            citas_PM.append(i) 
        elif "15:00" in i:
            citas_PM.append(i) 
        elif "16:00" in i:
            citas_PM.append(i) 
        elif "17:00" in i:
            citas_PM.append(i) 

        elif "00:00" in i:
            continue
        elif "1:00" in i:
            continue
        elif "2:00" in i:
            continue
        elif "3:00" in i:
            continue
        elif "4:00" in i:
            continue
        elif "5:00" in i:
            continue
        elif "6:00" in i:
            continue
        elif "7:00" in i:
            continue
    #Se verifica la intención del usuario
    if decision == "mañana":
        if len(citas_AM) > 0:
            respuesta = ""
            cont = 1
            for i in citas_AM:
                respuesta = respuesta + str(cont) + ". " + i + "\n"
                cont = int(cont) + 1
            bot.send_message(palabras.chat.id, "Tenemos disponibilidad para agendamiento de examen médico los siguientes días, por favor selecciona la opción que prefieras: " )
            bot.send_message(palabras.chat.id, respuesta )
            bot.register_next_step_handler(palabras, seleccion_cita_am)
        else:
            del users[chat_id]
            del last_active[chat_id]
            response = "no hay disponibilidad para ese día"
            bot.send_message(palabras.chat.id, response )
    elif decision == "tarde":
        if len(citas_PM) > 0:
            respuesta = ""
            cont = 1
            for i in citas_PM:
                respuesta = respuesta + str(cont) + ". " + i + "\n"
                cont = int(cont) + 1
            bot.send_message(palabras.chat.id, "Tenemos disponibilidad para agendamiento de examen médico los siguientes días, por favor selecciona la opción que prefieras: " )
            bot.send_message(palabras.chat.id, respuesta )
            bot.register_next_step_handler(palabras, seleccion_cita_pm)
        else:
            del users[chat_id]
            del last_active[chat_id]
            response = "no hay disponibilidad para ese día"
            bot.send_message(palabras.chat.id, response )
    elif decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    else:
        response = "Perdón, no entiendo que me quieres decir ¿Podrías volver a escribirlo?"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, bot_fecha)

#función de selección de citas en horarios de la mañana
def seleccion_cita_am(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    elif int(palabra) > len(citas_AM):
        response = "Perdón, no entiendo que me quieres decir ¿Podrías volver a escribirlo?"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, seleccion_cita_am)
    elif palabra  == "1":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[0] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])
                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[0])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[0] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[0])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "2":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[1] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[1])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[1] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[1])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()


    elif palabra == "3":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[2] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[2])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[2] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[2])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()
    elif palabra =="4":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[3] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[3])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[3] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[3])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()
    elif palabra  == "5":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[4] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[4])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[4] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[4])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "6":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[5] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[5])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[5] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[5])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "7":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[6] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[6])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[6] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[6])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()
    elif palabra =="8":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[7] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[7])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[7] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[7])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()
    elif palabra  == "9":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[8] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[8])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[8] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[8])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "10":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[9] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[9])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[9] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[9])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "11":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[10] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[10])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[10] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[10])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()
    elif palabra =="12":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_AM[11] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[11])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_AM[11] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_AM[11])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

#función de selección de citas de la tarde 
def seleccion_cita_pm(palabras):
    #Extrer chat id y texto
    chat_id = palabras.chat.id
    palabra = palabras.text.lower()
    #Se guarada el tiempo de inactividad 
    last_active[chat_id] = time.time()
    time_out = threading.Timer(1,check_inactive_users)
    time_out.start()
    decision = knn_clasificador(palabra, entrenamiento)# Lectura de palabra escrita po el usuario
    #Se verifica la intención del usuario
    if decision == "despedida": 
        del users[chat_id]
        del last_active[chat_id]
        response = "Si necesitas ayuda en cualquier cosa dejamelo saber."
        bot.send_message(palabras.chat.id, response )
    elif int(palabra) > len(citas_PM):
        response = "Perdón, no entiendo que me quieres decir ¿Podrías volver a escribirlo?"
        bot.send_message(palabras.chat.id, response )
        bot.register_next_step_handler(palabras, seleccion_cita_pm)
    elif palabra  == "1":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[0] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])
                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[0])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[0] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])
                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[0])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "2":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[1] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])
                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[1])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[1] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])
                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[1])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "3":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[2] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])
                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[2])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[2] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])
                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[2])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra =="4":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[3] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[3])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[3] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                esponse = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[3])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra =="5":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[4] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[4])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[4] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[4])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()
    elif palabra  == "6":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[5] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[5])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[5] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[5])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "7":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[6] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[6])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[6] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[6])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "8":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[7] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[7])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[7] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[7])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra =="9":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[8] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[8])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[8] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[8])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra =="10":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[9] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[9])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[9] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[9])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra  == "11":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[10] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[10])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[10] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[10])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "12":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[11] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[11])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[11] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[11])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra == "13":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[12] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[12])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[12] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[12])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra =="14":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[13] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[13])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[13] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                esponse = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[13])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()

    elif palabra =="15":
        if paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "1":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_uno" : citas_PM[14] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_1(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[14])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_uno":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"][0:], "%A %d/%m/%Y %H:%M"))})
                documento_agendamiento.update({"chat_id": chat_id})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_uno"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        elif paciente_f[users[chat_id]["documento_agendamiento"]]["cita_uno_agendar"] == "2":
            paciente_f[users[chat_id]["documento_agendamiento"]] = {"chat_id" : chat_id, "fecha_dos" : citas_PM[14] , "cita_uno_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_uno_avisar"], "cita_dos_avisar": doc_dict[users[chat_id]["documento_agendamiento"]]["cita_dos_avisar"], "plantilla": doc_dict[users[chat_id]["documento_agendamiento"]]["plantilla"], "cita inicio" : "", "cita fin" : ""}
            paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"], paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"] = horario_cita(paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
            evento = evento_para_cancelar(palabras, None, users[chat_id]["documento_agendamiento"])
            if evento == None:
                agendar_evento_2(palabras, None, paciente_f[users[chat_id]["documento_agendamiento"]]["cita inicio"] , paciente_f[users[chat_id]["documento_agendamiento"]]["cita fin"], users[chat_id]["documento_agendamiento"], users[chat_id]["email"])

                response = "La cita ha sido agendada para el día {0}. Si por algún motivo no puedes asistir a la cita, la puedes cancelar 24 horas antes".format(citas_PM[14])
                bot.send_message(palabras.chat.id, response )
                documento_agendamiento = doc_ref.document(users[chat_id]["documento_agendamiento"])
                documento_agendamiento.update({"fecha_dos":  str(datetime.strptime( paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"][0:], "%A %d/%m/%Y %H:%M"))})
                programar_mensaje(palabras.chat.id, paciente_f[users[chat_id]["documento_agendamiento"]]["fecha_dos"])
                del users[chat_id]
                del last_active[chat_id]
            else:
                del users[chat_id]
                del last_active[chat_id]
                response = "Ya tienes una cita agendada, si deseas cancelarla, házmelo saber"
                bot.send_message(palabras.chat.id, response )
        t1 = threading.Thread(name="read_data", target=read_data)
        t1.start()
    
#Recordatorio de cita programada
def programar_mensaje(chat_id, inicio_cita):
    hora = datetime.now()
    hora_envio = hora #datetime.strptime(inicio_cita[0:], "%A %d/%m/%Y %H:%M") - timedelta(hours=24)
    mensaje_programado = "¡Hola! recuerda que tienes una cita agendadada para el {}".format(inicio_cita)
    # Se ejecuta la función enviar_mensaje en la hora programada
    threading.Timer((hora_envio - hora.now()).total_seconds(), enviar_mensaje, args=[chat_id, mensaje_programado]).start()

#Recordatorio de calificación del servicio 
def programar_mensaje_plantila(chat_id, inicio_cita):
    hora = datetime.now()
    hora_envio = hora #inicio_cita + timedelta(hours=24)
    mensaje_programado = "¡Hola! Queremos saber que tal te pareció la plantilla y el servicio de footlab, te agradeceríamos si puedes calificar la experiencia con el laboratorio, accede a este link https://laboratoriobaspifootlab.tech/TESIS/templatemo/Iniciars.html, inicia sesión y en la columna en la izquierda encontrarás califica tu experiencia.\n Recuerda que puedes volver a agendar una cita para realizar seguimiento de avance y de plantilla"
    # Se ejecuta la función enviar_mensaje en la hora programada
    threading.Timer((hora_envio - hora.now()).total_seconds(), enviar_mensaje, args=[chat_id, mensaje_programado]).start()

def enviar_mensaje(chat_id, mensaje):
    bot.send_message(chat_id, mensaje)

#Loop infinito telegram
def recibir_mensaje():
    bot.infinity_polling()

if __name__ == "__main__":
    print("Iniciando el bot")
    lock = threading.Lock()
    funcionamiento = threading.Thread(name = "funcionamiento", target = recibir_mensaje)
    funcionamiento.start()
    print("Ya está funcionando")

