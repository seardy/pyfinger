import time
from pyfingerprint.pyfingerprint import PyFingerprint
import paho.mqtt.client as paho
import json
from service import marcar_asistencia, registro, eliminar


class Fingerprint:
    sensor = None
    client = paho.Client("sensor")
    abort = False

    def message(self, client, userdata, message):
        print(message.topic)
        if message.topic == "enroll/begin":
            self.abort = True

    def __init__(self):
        """

        :rtype:
        """
        try:
            self.sensor = PyFingerprint('/dev/ttyS0', 57600, 0xFFFFFFFF, 0x00000000)
            self.client.connect("localhost")
            # self.client.subscribe("enroll/begin")
            # self.client.on_message = self.message
            if not self.sensor.verifyPassword():
                raise ValueError('The given fingerprint sensor password is wrong!')

        except Exception as e:
            print('The fingerprint sensor could not be initialized!')
            print('Exception message: ' + str(e))
            exit(1)

    def search(self):
        try:
            print('Waiting for finger...')
            # Event waiting
            self.client.publish("search/waiting", "Coloque su dedo indice")

            # Wait until a finger is read
            while not self.sensor.readImage() and self.abort is False:
                pass
            # If not abort
            if self.abort is True:
                return
            else:
                self.client.connect("localhost")
                # Event processing
                self.client.publish("search/processing", "")

                # Converts read image to characteristics and stores it in char buffer 1
                self.sensor.convertImage(0x01)

                # Search for template in Ox01
                result = self.sensor.searchTemplate()

                # Position of the template found, if not found it's -1
                position_number = result[0]

                # Accuracy of the search
                accuracy_score = result[1]

                if position_number == -1:
                    # Send signal to monitor app, to communicate has not been found.
                    print('No match found!')
                    # Event notFound
                    self.client.publish("search/notFound", "Not Found")
                else:
                    # Send signal to monitor app to communicate user found
                    # Send signal to Api to store Assistance.
                    # Event found
                    datos = marcar_asistencia(position_number)

                    if not datos is False:
                        self.client.publish("search/found", json.dumps(datos))
                        return
                    else:
                        # Arroja getitem
                        self.client.publish("search/error", "Operacion Fallida")
                        print('Found template at position #' + str(position_number))
                        print('The accuracy score is: ' + str(accuracy_score))
        except IOError as e:
            print("Cachado hijueputa")
            print(e.message)
        except Exception as e:
            print('Operation failed!')
            print('Exception message: ' + str(e))
            # Event Error
            self.client.publish("search/error", "Operacion Fallida")

    def enroll(self, identificacion):
        try:
            self.abort = False
            print("Enroll: Waiting for finger...")
            self.client.connect("localhost")
            # Event waiting No 1
            self.client.publish("enroll/waiting", "Coloque su dedo indice")
            cont = 0
            # Block until finger is detected
            while not self.sensor.readImage() or cont <= 10:
                time.sleep(1)
                cont += 1
                pass
            if cont > 10:
                print("Abrete")
                return
            # Event processing No 1
            self.client.publish("enroll/processing", "")
            # Convert image to buffer for search if exists
            self.sensor.convertImage(0x01)

            # Store result of search, -1 if not found.
            result = self.sensor.searchTemplate()

            # Check if template exists
            if not result[0] == -1:
                # Send signal to monitor app
                print("Fingerprint exists..")
                # Event existe huella
                self.client.publish("enroll/exist", "Existe registro de la huella")
                return

                # Send signal to remove finger
            print('Remove finger...')
            time.sleep(2)

            # Send signal to put same finger
            print('Waiting for same finger again...')
            # Event waiting No 2
            self.client.publish("enroll/waiting", "Vuelva a colocar su dedo indice")

            # Block until finger is detected
            while not self.sensor.readImage():
                pass

            # Event processing No 2
            self.client.publish("enroll/processing", "")

            # Convert image to characteristic in char_buffer 0x02
            self.sensor.convertImage(0x02)

            if self.sensor.compareCharacteristics() == 0:
                # Send signal that Fingers do not match and must restart process
                # Event Huellas distintas --- raise Exception('Fingers do not match') ---
                self.client.publish("enroll/distint", "Huellas distintas")
                return

            # Create template to store
            self.sensor.createTemplate()

            # Store and retrieve position
            position = self.sensor.storeTemplate()

            registro(position, identificacion)
            # Send signal to show success in monitor
            print('Finger enrolled successfully!')
            # Event Operacion existosa
            self.client.publish("enroll/successful", "Operacion exitosa")
            # Send signal to backend for storing position
            print('New template position #' + str(position))
        except Exception as e:
            print(str(e))

    def delete(self, position):
        try:
            result = self.sensor.deleteTemplate(position)
            if result:
                # Consumir evento en el test.py
                eliminar(position)
                # Send signal to backend that has been deleted correctly.
                print('Template deleted!')

        except Exception as e:
            print(str(e))

    def clear_database(self):
        self.sensor.clearDatabase()
