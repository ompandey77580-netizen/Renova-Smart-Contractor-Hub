"""notify.py - tiny in-app notification helper (FR20)."""
import database

def notify(user_id, text):
    """Store one message for the bell icon on the dashboard."""
    database.execute(
        "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
        (user_id, text))

# called from:
#   bids.place_bid        -> notify(project.client_id, "New bid on ...")
#   bids.accept_bid       -> notify(contractor.user, "You were hired!")
#   contracts.mark_complete -> notify(client, "Milestone ready to approve")
#   payments.pay_milestone  -> notify(contractor.user, "Payment received")
