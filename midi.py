import pygame.midi as pm

def init():
    pm.init()

def close():
    pm.quit()

def outDevices():
    """Returns a list of tuples: (device name, output device number)"""
    return [(pm.get_device_info(device_id)[1], device_id)
            for device_id in range(pm.get_count())
            if pm.get_device_info(device_id)[3]==1]

def inDevices():
    """Returns a list of tuples: (device name, input device number)"""
    return [(pm.get_device_info(device_id)[1], device_id)
            for device_id in range(pm.get_count())
            if pm.get_device_info(device_id)[2]==1]
