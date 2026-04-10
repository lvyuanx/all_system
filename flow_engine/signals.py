from django.dispatch import Signal

# Triggered when a flow instance reaches FINISHED status.
flow_instance_finished_signal = Signal()
