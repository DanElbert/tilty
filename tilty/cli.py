# -*- coding: utf-8 -*-
""" Main Click methods """

import configparser
import logging
import pathlib
import signal
import sys
import threading
from functools import partial
from time import sleep
from typing import List

import click

from tilty import tilt_device
from tilty.exceptions import ConfigurationFileNotFoundException
from tilty.tilty import LOGGER, emit, parse_config

CONFIG = configparser.ConfigParser()


def terminate_process(
    device: tilt_device.TiltDevice,
    signal_number: int,
    frame: None
):  # noqa  # pylint: disable=unused-argument
    """ handle SIGTERM

    Args:
        device (TiltDevice): The bluetooth device to operate on.
        signal_number (int): The signal to operate on
        frame (TODO): The TODO

    """
    device.stop()
    sys.exit()


def scan_and_emit(device: tilt_device.TiltDevice, emitters: List[dict]):
    """ Scans and emits the data via the loaded emitters.

    Args:
        device (TiltDevice): The bluetooth device to operate on.
        emitters ([dict]): The emitters to use.
    """
    LOGGER.debug('Starting device scan')
    tilt_data = device.scan_for_tilt_data()
    if len(tilt_data) > 0:
        LOGGER.debug('tilt data retrieved')
        for datum in tilt_data:
            click.echo(datum)
        emit(emitters=emitters, tilt_data=tilt_data)
    else:
        LOGGER.debug('No tilt data')


def scan_and_emit_thread(
    device: tilt_device.TiltDevice,
    config: configparser.ConfigParser,
    keep_running: bool = False
) -> None:
    """ method that calls the needful

    Args:
        device (TiltDevice): The bluetooth device to operate on.
        config (dict): The parsed configuration
        keep_running (bool): Whether or not to keep running. Default: False
    """
    emitters = parse_config(config)
    click.echo('Scanning for Tilt data...')
    scan_and_emit(device, emitters)
    while keep_running:
        LOGGER.debug('Scanning for Tilt data...')
        scan_and_emit(device, emitters)
        sleep_time = int(CONFIG['general'].get('sleep_interval', '1'))
        LOGGER.debug('Sleeping for %s....', sleep_time)
        sleep(sleep_time)


@click.command()
@click.option(
    '--keep-running',
    '-r',
    is_flag=True,
    help="Keep running until SIGTERM",
)
@click.option(
    '--config-file',
    '-c',
    default='config.ini',
    help="configuration file path",
)
def run(
    keep_running: bool,
    config_file: str = 'config.ini',
):
    """
    main cli entrypoint

    Args:
        keep_running (bool): Whether or not to keep running. Default: False
        config_file (str): The configuration file location to load.
    """
    file = pathlib.Path(config_file)
    if not file.exists():
        raise ConfigurationFileNotFoundException()

    CONFIG.read(config_file)

    logging_level = 'INFO'
    try:
        logging_level = CONFIG['general'].get('logging_level', 'INFO')
    except KeyError:
        pass
    LOGGER.setLevel(logging.getLevelName(logging_level))

    device = tilt_device.TiltDevice()
    signal.signal(signal.SIGINT, partial(terminate_process, device))
    device.start()
    threading.Thread(
        target=scan_and_emit_thread,
        name='tilty_daemon',
        args=(device, CONFIG, keep_running)
    ).start()
    if keep_running:
        while True:
            pass
