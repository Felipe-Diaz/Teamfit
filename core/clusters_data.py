#Llamar a los datos desde la DB (Todo lo necesario)
#Implementar la limpieza()
#Realizar clusterización y almacenarla -> Puede guardar en una tabla distinta o modificar una tabla
#Nueva -> Foreign Key -> Proyectos con el tipo
from .models import proyectosAAgrupar, HorasPredecidas, proyectosSemanas


def realizar_clusterizacion():
    proyectos = proyectosAAgrupar.objects.all().order_by('id')
    horas = HorasPredecidas.objects.all().order_by('id')
    
    for proy in proyectos:
        
        horas_filtradas = horas.filter(
            linea_negocio=proy.lineaNegocio, 
            tipo=proy.tipo
        )
        print(horas_filtradas)
        for hora in horas_filtradas:
            proyectosSemanas.objects.update_or_create(
                semana=1,
                tipoSemana='Inicial',
                horas=hora,
                proyecto=proy
            )
    print('Hecho')
    return True
    

