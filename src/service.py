from datetime import datetime, timedelta
from pymongo import MongoClient

def marcar_asistencia(id):
    # Coleccion de datos de los empleados
    mongo = MongoClient("mongodb://testing:test@ds155934.mlab.com:55934/testing_this_shit?authMechanism=SCRAM-SHA-1")
    user = mongo.db.users
    # Datos enviados en la peticion post para llenar la asistencia
    fecha = datetime.now()
    dia = fecha.weekday()
    hora = fecha.hour
    minutos = fecha.minute

    found = user.aggregate([
        {'$match': {'id': id}},
        {'$unwind': "$regla"},
        {'$match': {"regla.dia": dia}}
    ])

    rules = list(found)

    # Creamos un vector para guardar los resultados
    results = []

    for rule in rules:
        # Obtenemos la hora de la regla
        hora_rule = rule['regla']['hora']
        # Convertimos la hora de string a datetime
        time_rule = datetime.strptime(hora_rule, '%H:%M')
        # Obtenemos el tiempo actual
        now = datetime.now()
        # Comparamos las dos
        my_time = now.replace(hour=time_rule.time().hour, minute=time_rule.time().minute,
                              second=time_rule.time().second, microsecond=0)
        # Obtenemos la diferencia entre las dos horas.
        diff = my_time - now
        # Guardamos el id de la regla y el resultado en el vector
        results.append({'id': rule['regla']['idRegla'], 'diff': diff.total_seconds()})

    # Ordenamos el vector por el valor diff
    results.sort(key=lambda x: x['diff'])

    # Aqui guardaremos la regla escogida para hacer la comparacion
    chosen_rule = None

    for rule in rules:
        if rule['regla']['idRegla'] == results[0]['id']:
            chosen_rule = rule['regla']

    # Se convierte la hora de string a datetime
    rule_t = datetime.strptime(chosen_rule['hora'], '%H:%M')

    # Configuramos el datetime rule_t para que tome la fecha actual
    rule_t = now.replace(
        hour=rule_t.time().hour,
        minute=rule_t.time().minute,
        second=rule_t.time().second,
        microsecond=0)

    # Creamos un limite inferior de tolerancia
    inf_limit = rule_t - timedelta(minutes=15)

    # Creamos un limite superior de tolerancia
    sup_limit = rule_t + timedelta(minutes=15)

    # Comprobamos si la hora actual se encuentra en el rango
    atiempo = now >= inf_limit and now <= sup_limit

    # Busqueda de la id del empleado pasados en la url
    user_found = user.find_one({'id': id})

    # Preparando la informacion a guardar
    asistencia = {
        'fecha': fecha,
        'tipo': chosen_rule['tipo'],
        'atiempo': atiempo
    }

    # Operacion que agrega la nueva asistencia del empleado
    user_found['asistencia'].append(asistencia)

    # Guardar los cambios en la base de datos
    user.save(user_found)