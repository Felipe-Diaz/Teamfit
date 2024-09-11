#Llamar a los datos desde la DB (Todo lo necesario)
#Implementar la limpieza()
#Realizar clusterización y almacenarla -> Puede guardar en una tabla distinta o modificar una tabla
#Nueva -> Foreign Key -> Proyectos con el tipo

def realizar_clusterizacion():
    print('Realizando Limpieza')
    errores = False
    errores = realizar_limpieza()
    errores = realizar_caracterizacion()
    errores = realizar_clusterizacion()
    if(errores):
        print('No se ha logrado realizar la clusterizacion')
    else:
        print('Se ha realizado la limpieza')
        return True
    
    
def realizar_limpieza():
    print('Realizando Limpieza')
    return False

def realizar_caracterizacion():
    print('Realizando Caracterización')
    return False
    
def guardar_clusterizacion():
    print('Guardando Datos')
    return False