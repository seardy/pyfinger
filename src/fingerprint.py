import time
from pyfingerprint.pyfingerprint import PyFingerprint
import paho.mqtt.client as paho

from service import marcar_asistencia

class Fingerprint:
    
    sensor = None
    client = paho.Client("sensor")

    def __init__(self):
        """

        :rtype:
        """
        try:
            self.sensor = PyFingerprint('/dev/ttyS0', 57600, 0xFFFFFFFF, 0x00000000)
            self.client.connect("localhost")

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
            self.client.publish("search/waiting", "ponga su huella")

            # Wait until a finger is read
            while not self.sensor.readImage():
                pass
            #Event processing 
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
                #Event notFound
                self.client.publish("search/notFound", "Not Found")
            else:
                # Send signal to monitor app to communicate user found
                # Send signal to Api to store Assistance.
                #Event found
                if marcar_asistencia(position_number):
                    self.client.publish("search/found", str(position_number))
                else:
                    self.client.publish("search/error", "Operacion Fallida")
                print('Found template at position #' + str(position_number))
                print('The accuracy score is: ' + str(accuracy_score))
        except Exception as e:
            print('Operation failed!')
            print('Exception message: ' + str(e))
            #Event Error 
            self.client.publish("search/error", "Operacion Fallida")

    def enroll(self):
        try:
            print("Waiting for finger...")

            # Block until finger is detected
            while not self.sensor.readImage():
                pass

            # Convert image to buffer for search if exists
            self.sensor.convertImage(0x01)

            # Store result of search, -1 if not found.
            result = self.sensor.searchTemplate()

            # Check if template exists
            if not result == -1:
                # Send signal to monitor app
                print("Fingerprint exists..")

            # Send signal to remove finger
            print('Remove finger...')
            time.sleep(2)

            # Send signal to put same finger
            print('Waiting for same finger again...')

            # Block until finger is detected
            while not self.sensor.readImage():
                pass

            # Convert image to characteristic in char_buffer 0x02
            self.sensor.convertImage(0x02)

            if self.sensor.compareCharacteristics() == 0:
                # Send signal that Fingers do not match and must restart process
                raise Exception('Fingers do not match')

            # Create template to store
            self.sensor.createTemplate()

            # Store and retrieve position
            position = self.sensor.storeTemplate()

            # Send signal to show success in monitor
            print('Finger enrolled successfully!')

            # Send signal to backend for storing position
            print('New template position #' + str(position))

        except Exception as e:
            print(str(e))

    def delete(self, position):
        try:
            result = self.sensor.deleteTemplate(position)
            if result:
                # Send signal to backend that has been deleted correctly.
                print('Template deleted!')

        except Exception as e:
            print(str(e))
