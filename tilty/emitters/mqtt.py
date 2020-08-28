# -*- coding: utf-8 -*-
""" mqtt emitter """
import logging

import paho.mqtt.client as mqtt
from jinja2 import Template

LOGGER = logging.getLogger()

def on_connect(mqttc, obj, flags, rc):
    LOGGER.debug("[mqtt] connected. rc: " + str(rc))

def __type__() -> str:
    return 'Mqtt'

class Mqtt:  # pylint: disable=too-few-public-methods
    """ Mqtt wrapper class """

    def __init__(self, config: dict) -> None:
        """ Initializer

        Args:
            config: (dict) represents the configuration for the emitter
        """
        # <start config sample>
        # [mqtt]
        # host = mqtt.example.com
        # user = mqtt
        # password = secret
        # topic = tilt
        # payload_template = {"color": "{{ color }}", "gravity"...
        # client_id = abc123
        # port = 1883

        self.template: Template = Template(config['payload_template'])
        self.topic: str = config['topic']

        self.mqtt_client = mqtt.Client(client_id=config['client_id'])
        self.mqtt_client.username_pw_set(config['user'], config['password'])
        self.mqtt_client.on_connect = on_connect


        self.mqtt_client.connect(config['host'], port=int(config['port']))
        self.mqtt_client.loop_start()

    def emit(self, tilt_data: dict) -> None:
        """ Initializer

        Args:
            tilt_data (dict): data returned from valid tilt device scan
        """

        payload: str = self.template.render(
            color=tilt_data['color'],
            gravity=tilt_data['gravity'],
            mac=tilt_data['mac'],
            temp=tilt_data['temp'],
            timestamp=tilt_data['timestamp'],
        )


        LOGGER.info('[mqtt] publishing message')
        infot = self.mqtt_client.publish(self.topic, payload)
        infot.wait_for_publish()
    
    
