import json
from os import scandir
from sys import argv, stderr
import requests
from lxml.html.clean import Cleaner
from lxml import html
from lxml import etree

# globales

dict = {}
lista_ficheros = []
indexado = False
dic_web = {}

# rastreo web


def get_clean_page(text):
    cleaner = Cleaner()
    cleaner.javascript = True  # This is True because we want to activate the javascript filter
    cleaner.style = True  # This is True because we want to activate the styles & stylesheet filter
    cleaner.comments = True
    page = html.fromstring(cleaner.clean_html(text),
                           parser=etree.HTMLParser(remove_blank_text=True, remove_comments=True, remove_pis=True,
                                                   strip_cdata=True))

    return ' '.join(page.xpath('//body//text()'))


# union e interseccion listas


def union_listas(l1, l2):
    lista = []
    for elem in l1:
        if elem not in l2:
            lista.append(elem)
    lista = lista + l2

    return lista


def union_varias_listas(M):
    for i in range(len(M)):
        for j in range(len(M[i])):
            union = union_listas(M[0], M[1])
            for i in range(2, len(M)):
                union = union_listas(union, M[i])

    return union


def intersec_listas(l1, l2):
    lista = []
    for elem in l1:
        if elem in l2:
            lista.append(elem)

    return lista


def interseccion_varias_listas(M):
    for i in range(len(M)):
        for j in range(len(M[i])):
            intersec = intersec_listas(M[0], M[1])
            for i in range(2, len(M)):
                intersec = intersec_listas(intersec, M[i])

    return intersec


# snippet


def snippet(archivo, consulta):
    with open(archivo, 'r') as fich:
        for linea in fich:
            linea_depurada = []
            linea_separada = linea.split()
            for palabra in linea_separada:
                palabra = depurar_palabra(palabra)
                linea_depurada.append(palabra)
            for i in range(0, len(consulta.split()) + 1, 2):
                if consulta.split()[i] in linea_depurada:
                    linea_sin_espacios = []
                    for palabra in linea_separada:
                        if palabra != ' ':
                            linea_sin_espacios.append(palabra)

                    cad = ''
                    for i in range(len(linea_sin_espacios)):
                        cad += linea_sin_espacios[i] + ' '
                    print('\t' + cad + '\n')
                    return


# preprocesar palabras


def eliminar_acentos(palabra):
    acentos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u'}
    for c in acentos:
        palabra = palabra.replace(c, acentos[c])
    return palabra


def eliminar_especial(cadena):
    palabra = ''
    noespeciales = '1234567890abcdefghijklmnñopqrstuvwxyz '
    for c in cadena:
        if c in noespeciales:
            palabra += c
    return palabra


def depurar_palabra(cadena):
    cadena = cadena.lower()
    primera = eliminar_acentos(cadena)
    palabra = eliminar_especial(primera)
    return palabra


# indexar


def dame_archivos(directorio):
    lista = []
    with scandir(directorio) as dir:
        for fichero in dir:
            if fichero.is_dir():
                lista.extend(dame_archivos(fichero.path))
            elif fichero.is_file():
                lista.append(fichero.path)
    return lista


def indexar_palabras(lista, diccionario, id_fichero):
    for palabra in lista:
        palabra = depurar_palabra(palabra)
        if len(palabra) > 0:
            if palabra not in diccionario:
                diccionario[palabra] = [id_fichero]
            else:
                list_docs = diccionario[palabra]
                if id_fichero != list_docs[-1]:
                    list_docs.append(id_fichero)


def indexar_documentos(diccionario, lista_ficheros, id):

    with open(lista_ficheros[id], 'r') as fichero:
        for linea in fichero:
            palabras = linea.split()
            indexar_palabras(palabras, diccionario, id)


def busqueda(consulta, diccionario):
    resultado = []
    palabras = consulta.split()
    for palabra in palabras:
        if palabra not in ['and', 'or']:
            palabra = depurar_palabra(palabra)
            if len(palabra) != 0 and palabra in diccionario:
                resultado.append(diccionario[palabra])

    return resultado


def guardar_indice(ruta, diccionario, lista_de_archivos):
    indice_y_archivos = {}
    indice_y_archivos['indice'] = diccionario
    indice_y_archivos['archivos'] = lista_de_archivos
    with open(ruta, 'w') as f:
        json.dump(indice_y_archivos, f, indent=4, ensure_ascii=False)


def cargar_indice(ruta):
    try:
        with open(ruta, 'r') as f:
            indice_y_archivos = json.load(f)
            return indice_y_archivos['indice'], indice_y_archivos['archivos']

    except FileNotFoundError:
        print('El fichero {0} no existe.'.format(ruta))
        return {}, []


# buscador


def menu_principal():
    print('''
    Menú principal.
    ---------------
    1. Indexar documentos.
    2. Buscar.
    3. Guardar índice.
    4. Cargar índice.
    5. Indexar webs.
    6. Salir.
    ''')


def menu_secundario():
    print('''
        ¿Qué desea hacer?
        -----------------
        1. Ver un documento.
        2. Ver diez documentos más.
        3. Volver al menú principal.
        ''')


def buscador(diccionario, lista_ficheros):
    global indexado, dic_web

    while True:
        menu_principal()
        opcion_1 = int(input('Elige una opción: '))

        if opcion_1 == 1:
            lista_ficheros = dame_archivos(argv[1])
            for id in range(len(lista_ficheros)):
                indexar_documentos(diccionario, lista_ficheros, id)
            print('Indexado correctamente.\n')
            indexado = True

        elif opcion_1 == 2:
            consulta = input('Palabra/s a buscar: ').lower()
            if len(consulta.split()) == 1:
                if depurar_palabra(consulta) not in diccionario:
                    print('La palabra buscada no se encuentra en nigún archivo de ' + argv[1] + '.')
                else:
                    r = busqueda(consulta, diccionario)
                    resultado = r[0]
                    dic = {}
                    for k in range(len(resultado)):
                        dic[k] = lista_ficheros[resultado[k]]

                    print('\nSe han encontrado ' + str(len(resultado)) + ' resultados en ' + argv[1] + '.')

                    if len(resultado) <= 10:
                        print('\nMostrando del 1 al ' + str(len(resultado)) + ': ')
                        for i in range(len(dic)):
                            print(str(i + 1) + '. ' + dic[i])
                            snippet(dic[i], depurar_palabra(consulta))
                    else:
                        print('Mostrando del 1 al 10: ')
                        for i in range(10):
                            print(str(i+1) + '. ' + dic[i])
                            snippet(dic[i], depurar_palabra(consulta))

                if dic_web != {}:
                    resultados_web = []
                    for ruta in dic_web:
                        if depurar_palabra(consulta) in dic_web[ruta]:
                            resultados_web.append(ruta)

                    if len(resultados_web) == 1:
                        print('La palabra está en la página web: ' + str(resultados_web[0]))
                    elif len(resultados_web) > 1:
                        print('La palabra está en las páginas web: ')
                        for elem in resultados_web:
                            print(elem)
                    else:
                        print('La palabra no está en ninguna página web indexada.')

            else:
                resul = busqueda(consulta, diccionario)

                if 'or' in depurar_palabra(consulta):
                    resultado = union_varias_listas(resul)
                    dic = {}
                    for k in range(len(resultado)):
                        dic[k] = lista_ficheros[resultado[k]]

                    print('\nSe han encontrado', len(resultado), 'resultados en ' + argv[1] + '.')

                    if len(resultado) <= 10:
                        print('Mostrando del 1 al ' + str(len(resultado)) + ': ')
                        for i in range(len(dic)):
                            print(str(i + 1) + '. ' + dic[i])
                            snippet(dic[i], depurar_palabra(consulta))
                    else:
                        print('Mostrando del 1 al 10: ')
                        for i in range(10):
                            print(str(i + 1) + '. ' + dic[i])
                            snippet(dic[i], depurar_palabra(consulta))

                    if dic_web != {}:
                        resultados_web1 = []
                        for i in range(0, len(depurar_palabra(consulta).split()), 2):
                            for ruta in dic_web:
                                if depurar_palabra(consulta).split()[i] in dic_web[ruta]:
                                    resultados_web1.append(ruta)

                        resultados_web2 = []
                        for elem in resultados_web1:
                            if elem not in resultados_web2:
                                resultados_web2.append(elem)

                        if len(resultados_web2) == 1:
                            print('Las palabras están en la página web: ' + str(resultados_web2[0]))
                        elif len(resultados_web2) > 1:
                            print('Las palabras están en alguna de las páginas web: ')
                            for elem in resultados_web2:
                                print(elem)
                        else:
                            print('Ninguna palabra está en las páginas web indexadas.')

                elif 'and' in depurar_palabra(consulta):
                    resultado = interseccion_varias_listas(resul)
                    dic = {}
                    for k in range(len(resultado)):
                        dic[k] = lista_ficheros[resultado[k]]

                    print('\nSe han encontrado', len(resultado), 'resultados en ' + argv[1] + '.')

                    if len(resultado) <= 10:
                        print('Mostrando del 1 al ' + str(len(resultado)) + ': ')
                        for i in range(len(dic)):
                            print(str(i + 1) + '. ' + dic[i])
                            snippet(dic[i], depurar_palabra(consulta))
                    else:
                        print('Mostrando del 1 al 10: ')
                        for i in range(10):
                            print(str(i + 1) + '. ' + dic[i])
                            snippet(dic[i], depurar_palabra(consulta))

                    if dic_web != {}:
                        resultados_web3 = []
                        for i in range(0, len(depurar_palabra(consulta).split()), 2):
                            for ruta in dic_web:
                                if depurar_palabra(consulta).split()[i] in dic_web[ruta]:
                                    resultados_web3.append(ruta)

                        repetidos = []
                        unicos = []
                        for ruta in resultados_web3:
                            if ruta not in unicos:
                                unicos.append(ruta)
                            else:
                                if ruta not in repetidos:
                                    repetidos.append(ruta)

                        if len(repetidos) == 1:
                            print('Las palabras están en la página web: ' + str(repetidos[0]))
                        elif len(repetidos) > 1:
                            print('Las palabras están a la vez en las páginas web: ')
                            for elem in repetidos:
                                print(elem)
                        else:
                            print('Las palabras no están en ninguna página web indexada conjuntamente.')

                else:
                    print('La entrada no es válida.')

            contador = 10
            while True:
                menu_secundario()
                opcion_2 = int(input('Elige una opción: '))

                if opcion_2 == 1:
                    num_ver = int(input('Introduce el número del documento que quieres leer: '))
                    if num_ver <= len(resultado):
                        try:
                            with open(dic[num_ver - 1], 'r') as fichero:
                                for linea in fichero:
                                    print(linea, end=' ')
                                print()

                        except FileNotFoundError:
                            print('El archivo', num_ver, 'no existe.', file=stderr)
                    else:
                        print('El fichero no está disponible en la búsqueda.')

                elif opcion_2 == 2:
                    if len(resultado) - contador <= 0:
                        print('No hay más resultados disponibles en ' + argv[1] + '.')

                    else:
                        if (len(resultado) - contador) < 10:
                            print('Mostrando del', contador + 1, 'al', len(resultado), ':')
                            for i in range(contador, len(dic)):
                                print(str(i + 1) + '. ' + dic[i])
                                snippet(dic[i], depurar_palabra(consulta))
                        else:
                            print('Mostrando del', contador + 1, 'al', contador + 10, ':')
                            for i in range(contador, contador + 10):
                                print(str(i + 1) + '. ' + dic[i])
                                snippet(dic[i], depurar_palabra(consulta))

                    contador += 10

                elif opcion_2 == 3:
                    break

                else:
                    print('Elige una opción válida.', file=stderr)

        elif opcion_1 == 3:
            if indexado:
                guardar_indice('indice.json', diccionario, lista_ficheros)
            else:
                print('No hay documentos indexados todavía para guardar.')

        elif opcion_1 == 4:
            diccionario, lista_ficheros = cargar_indice('indice.json')

        elif opcion_1 == 5:
            url = input('Introduce las páginas web a indexar (separadas por un espacio): ')
            rutas = url.split()
            for ruta in rutas:
                response = requests.get(ruta)
                dic_web[ruta] = []
                web_texto = get_clean_page(response.text)
                for palabra in web_texto.split():
                    palabra = depurar_palabra(palabra)
                    dic_web[ruta].append(palabra)

        elif opcion_1 == 6:
            break

        else:
            print('Elige una opción válida.', file=stderr)


buscador(dict, lista_ficheros)
