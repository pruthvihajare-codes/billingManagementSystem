from django import template
from billingManagementSystem.encryption import encrypt_parameter
import logging

register = template.Library()

@register.filter(name='enc')
def enc(value):
    try:
        return encrypt_parameter(str(value))
    except Exception as e:
        logging.exception("Encryption failed for value: %s", value)
        return ''
