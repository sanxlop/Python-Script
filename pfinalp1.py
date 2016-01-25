import os
import subprocess
import sys 

'''
Practica Parcial 1

En esta practica crearemos un escenario basado en VMs. El escenario sera el descrito en la practica 3 parte B. Constara de un cliente (C1), un balanceador de carga (lb), un numero X de servidores a determinar (s0,...,sX) con (0<X<6) y dos VLANs.
Para 
Para que el programa funcione correctamente es necesario crear el directorio /mnt/tmp/alberto.sanchez.lopez y ejecutarlo
desde ahi. El resto de configuraciones y el problema del arranque han sido automatizadas.
'''


''' Variables y constantes '''
server = 0
servers = ['s1', 's2', 's3', 's4', 's5']



''' FUNCION CREATE '''
def create():
	print "CREANDO....."
	#Copiamos en nuestra carpeta los imagen base y la plantilla xml
	os.system("cp /mnt/vnx/repo/cdps-vm-base-p3.qcow2.bz2 .")
	os.system("bunzip2 cdps-vm-base-p3.qcow2.bz2")
	os.system("cp /mnt/vnx/repo/plantilla-vm-p3.xml .")

	#Permite elegir numero de servidores para crear el escenario deseado
	while True:
		a = raw_input("Indique el numero de servidores con el que contara su escenario: ")
		server = int(a)
		#Creamos un archivo auxiliar que guardara el numero de servidores
		archi=open('nserver.txt','w')
		archi.close()
		archi=open('nserver.txt','a')
		archi.write(a)
		archi.close()

		#Comprobamos que el numero de servidores especificado es correcto
		if(server>0 and server<6):
			print 'Su entorno contara con ', server, " servidores."
			#Creamos la imagenes correspondientes a cada servidor junto con su xml. 
			#Comando sed, sustituye cadena2 en cadena1 en archivo indicado.
			for i in range(server):
				os.system('qemu-img create -f qcow2 -b cdps-vm-base-p3.qcow2 '+servers[i]+'.qcow2')
				os.system('cp plantilla-vm-p3.xml '+servers[i]+'.xml')
				os.system("sed -i '2 s/XXX/'"+servers[i]+"'/' "+servers[i]+".xml")
				os.system("sed -i '23 s/XXX/alberto.sanchez.lopez/' "+servers[i]+".xml")
				os.system("sed -i '23 s/XXX/'"+servers[i]+"'/' "+servers[i]+".xml")
				os.system("sed -i '27 s/XXX/LAN2/' "+servers[i]+".xml")
				print 'Se ha creado la imagen del servidor '+servers[i]+' con su XML correspondiente.'

			#Imagenes del balanceador y cliente en metodos externos
			createLb()

			createC1()

			#Bridges
			os.system("sudo brctl addbr LAN1")
			os.system("sudo brctl addbr LAN2")
			os.system("sudo ifconfig LAN1 up")
			os.system("sudo ifconfig LAN2 up")
			print "Los bridges han sido creados"
			print "Ahora arranque o destruya el escenario creado"
			return

		#Si no se introduce un numero valido de servidores, volvemos a pedirlo
		else:
			print 'Debe seleccionar un numero de servidores entre 1-5'


''' CREAR CLIENTE '''
def createC1():
	os.system('qemu-img create -f qcow2 -b cdps-vm-base-p3.qcow2 c1.qcow2')
	os.system('cp plantilla-vm-p3.xml c1.xml')
	os.system("sed -i '2 s/XXX/c1/' c1.xml")
	os.system("sed -i '23 s/XXX/alberto.sanchez.lopez/' c1.xml")
	os.system("sed -i '23 s/XXX/c1/' c1.xml")
	os.system("sed -i '27 s/XXX/LAN1/' c1.xml")
	
''' CREAR BALANCEADOR '''
def createLb():
	#Abrimos la plantilla solo en modo lectura
	source = open("plantilla-vm-p3.xml", "r")

	#Abrimos lb.xml habilitando la escritura al final del fichero.
	xml = open("lb.xml", "a")

	#Leemos la plantilla linea a linea
	doc = source.readlines()

	#Copiamos hasta la linea 29 (etiqueta interface)
	for i in range(29):
		xml.write(doc[i])

	#Copiamos de nuevo la etiqueta interface
	for i in range(25,29):
		xml.write(doc[i])

	#Copiamos el final de la plantilla
	for i in range(29,39):
		xml.write(doc[i])

	source.close()
	xml.close()

	os.system("qemu-img create -f qcow2 -b cdps-vm-base-p3.qcow2 lb.qcow2")
	os.system("sed -i '2 s/XXX/lb/' lb.xml")
	os.system("sed -i '23 s/XXX/alberto.sanchez.lopez/' lb.xml")
	os.system("sed -i '23 s/XXX/lb/' lb.xml")
	os.system("sed -i '27 s/XXX/LAN1/' lb.xml")
	os.system("sed -i '31 s/XXX/LAN2/' lb.xml")
	
	

''' FUNCION START '''
def start():

	archi=open('nserver.txt','r')
	lineas=archi.readlines()
	for li in lineas:
		server = int(li)
	archi.close()

	#Iniciamos las VM
	os.system('sudo virsh create lb.xml')
	os.system('sudo virsh create c1.xml')
	for i in range(server):
		os.system('sudo virsh create '+servers[i]+'.xml')
		print "VMs creadas"
	#Abrimos un terminal para cada maquina
	subprocess.Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs","10","-title","\"lb\"","-e","sudo","virsh","console","lb"])
	subprocess.Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs","10","-title","\"c1\"","-e","sudo","virsh","console","c1"])
	for i in range(server):
		subprocess.Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs","10","-title","\""+servers[i]+"\"","-e","sudo","virsh","console",servers[i]])

	print "Escenario creado con exito"

''' FUNCION STOP VM '''
def stop():
	#Variable: numero de servidores arrancados
	archi=open('nserver.txt','r')
	lineas=archi.readlines()
	for li in lineas:
		server = int(li)
	archi.close()

	#Paramos las maquinas de forma ordenada
	os.system("sudo virsh shutdown lb")
	os.system("sudo virsh shutdown c1")
	for i in range(server):
		os.system("sudo virsh shutdown "+servers[i])

	print "Escenario parado con exito"


''' FUNCION DESTROY '''
def destroy():
	#Variable: numero de servidores arrancados
	archi=open('nserver.txt','r')
	lineas=archi.readlines()
	for li in lineas:
		server = int(li)
	archi.close()

	#Paramos las maquinas bruscamente
	os.system("sudo virsh destroy lb")
	os.system("sudo virsh destroy c1")
	for i in range(server):
		os.system("sudo virsh destroy "+servers[i])

	#Eliminamos los ficheros xml y los archivos qcow2
	os.system("rm -f lb.xml")
	os.system("rm -f c1.xml")
	os.system("rm -f lb.qcow2")
	os.system("rm -f c1.qcow2")

	for i in range(server):
		os.system("rm -f "+servers[i]+".xml")
		os.system("rm -f "+servers[i]+".qcow2")

	#Liberamos los switches
	os.system('sudo ifconfig LAN1 down')
	os.system('sudo ifconfig LAN2 down')
	os.system('sudo brctl delbr LAN1')
	os.system('sudo brctl delbr LAN2')

	print "Escenario destruido con exito"

'''
Funcion visualizacion Virt Manager

Ejecuta el comando que abre la interfaz grafica del virt manager
'''
def virtManager():

	os.system("HOME=/mnt/tmp sudo virt-manager")



'''
Funcion de listado de maquinas virtuales

Ejecuta el comando virsh para listar las maquinas virtuales y su estado 
'''
def listar():

	os.system("sudo virsh list --all")


def hostname():

	os.system("mkdir mnt")
	os.system("sudo vnx_mount_rootfs -s -r s1.qcow2 mnt")	
	elegido = raw_input("Elija nuevo hostname:" )
	os.system("sed -i '1c "+elegido+"' mnt/etc/hostname")
	os.system("sed -i '2c 127.0.1.1       "+elegido+"' mnt/etc/hosts")
	return


atributo = sys.argv[1]
if atributo == "create":
	print "Espere mientras se generan los ficheros necesarios."	
	print "Esta accion puede tardar un poco..."
	create()
elif atributo == "start":
	start()
	start()
elif atributo == "display":
	virtManager()	
elif atributo == "stop":
	stop()
elif atributo == "destroy":
	destroy()
elif atributo == "list":
	listar()
elif atributo == "hostname":
	hostname()
else:
	print "Comando incorrecto."
	print "Opciones disponibles: create, start, stop, destroy, list, display, hostname"

