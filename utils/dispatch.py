from django.dispatch import (
    Signal,
    receiver,
)
from . import (
    Order,
    Merchant
)


# Signals

order_placed_signal = Signal(['place_id', 'branch_id', 'customer', 'order'])

order_changed_signal = Signal(['place_id', 'branch_id', 'customer', 'order'])

order_canceled_signal = Signal(['place_id', 'branch_id', 'customer', 'order'])

merchant_signup_signal = Signal(['merchant', 'place_id'])

customer_signup_signal = Signal(['merchant', 'place_id'])

new_branch_signal = Signal(['place_id', 'branch_id'])



# Handlers


@receiver(merchant_signup_signal, sender=Merchant)
def send_welcome_mail(sender, *args, **kwargs):
    pass


@receiver(order_changed_signal, sender=Order)
def send_order_notification_mail(sender, *args, **kwargs):
    pass


@receiver(order_placed_signal, sender=Order)
def send_welcome_mail(sender, *args, **kwargs):
    pass
