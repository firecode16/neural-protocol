# neural_protocol/constants.py
"""
Constantes globales para NeuralProtocol, incluyendo tipos de mensajes de control.
"""

# Tipos de mensajes de control para federación entre hubs
CTRL_FWD_SIGNAL = "fwd_signal"           # Reenvío de señal entre hubs
CTRL_HUB_REGISTER = "hub_register"       # Registro de un hub remoto
CTRL_HUB_PEER_UPDATE = "hub_peer_update" # Actualización de lista de agentes remotos

# Separador para identificadores globales de agentes (nombre@dominio)
GLOBAL_ID_SEPARATOR = "@"