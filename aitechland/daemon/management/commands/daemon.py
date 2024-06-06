from django.core.management.base import BaseCommand
import time


class Command(BaseCommand):
    help = 'Run a simple daemon'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting daemon...")
        while True:
            # Your daemon logic here
            self.stdout.write("Daemon is working...")
            time.sleep(10)  # Sleep for 10 seconds

            # Optional: Add condition to break the loop to stop the daemon
            # if condition:
            #     break

        self.stdout.write("Daemon stopped.")
