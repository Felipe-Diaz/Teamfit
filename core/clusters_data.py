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
        for hora in horas_filtradas:
            #print(f'{hora.linea_negocio} - {hora.tipo} - {hora.rol} - {hora.tipo_semana}')
            proyectosSemanas.objects.update_or_create(
                semana=1,
                tipoSemana=hora.tipo_semana,
                horas=hora,
                proyecto=proy
            )
    print('Hecho')
    return True
    

