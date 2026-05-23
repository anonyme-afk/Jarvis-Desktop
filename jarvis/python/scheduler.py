"""
Planificateur de tâches autonomes pour JARVIS.
Source : github.com/agronholm/apscheduler
pip install APScheduler
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import datetime
import os

class JARVISScheduler:
    def __init__(self, jarvis_callback):
        """
        jarvis_callback : fonction appelée avec (message, priority)
        priority : 'normal' | 'urgent' | 'wake_screen'
        """
        self.callback = jarvis_callback
        self.scheduler = BackgroundScheduler()
        self._register_default_tasks()

    def _register_default_tasks(self):
        # Briefing matinal : 7h00 du lundi au vendredi
        self.scheduler.add_job(
            self._morning_briefing,
            CronTrigger(day_of_week='mon-fri', hour=7, minute=0),
            id='morning_briefing', replace_existing=True
        )
        # Vérification des mails : toutes les 15 minutes
        self.scheduler.add_job(
            self._check_urgent_notifications,
            IntervalTrigger(minutes=15),
            id='check_notifications', replace_existing=True
        )
        # Rapport système : toutes les heures
        self.scheduler.add_job(
            self._system_health_check,
            IntervalTrigger(hours=1),
            id='system_health', replace_existing=True
        )

    def start(self):
        self.scheduler.start()
        print("[SCHEDULER] Planificateur démarré")

    def add_reminder(self, message: str, minutes: int):
        run_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        self.scheduler.add_job(
            lambda: self.callback(f"Rappel : {message}", "wake_screen"),
            'date', run_date=run_time,
            id=f"reminder_{run_time.timestamp()}"
        )

    def _morning_briefing(self):
        self.callback(
            "Bonjour Monsieur. Briefing matinal : météo, actualités et tâches du jour.",
            "wake_screen"
        )

    def _check_urgent_notifications(self):
        # À personnaliser : vérifier Gmail, Slack, Discord, etc.
        pass

    def _system_health_check(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            if cpu > 90:
                self.callback(
                    f"Alerte : CPU à {cpu}%. Analyse des processus recommandée.",
                    "urgent"
                )
            elif ram > 90:
                self.callback(
                    f"Alerte : RAM à {ram}% d'utilisation.",
                    "urgent"
                )
        except:
            pass

jarvis_scheduler = None  # Initialisé dans server.py
