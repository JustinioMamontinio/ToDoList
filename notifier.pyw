from database import Session
from models import Task
import plyer
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Логирование в файл
log_file = Path(__file__).parent / "notifier.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
class Notifier:
    def __init__(self):
        self.session = Session()

    def find_tasks(self):
        res = []
        now = datetime.now()
        tasks = self.session.query(Task).all()
        for task in tasks:
           if task.deadline is not None and not task.is_done and now < task.deadline <= now + timedelta(days = 1):
                res.append(task)
        return res
    
    def send_notification(self, task: Task):
        remaining = task.deadline - datetime.now()

        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        plyer.notification.notify(title = f"До срока выполнения задачи осталось {hours}ч {minutes}мин",
                                  message = f'Срок выполнения задачи {task.title} ({task.description})\
                                  всего {hours}ч {minutes}мин. \n Поторопись!',
                                  timeout = 5)
    def run(self):
        deadline = [timedelta(minutes = 5), timedelta(minutes = 30), timedelta(hours = 2), timedelta(days = 1)]
        tasks = self.find_tasks()
        tasks.sort(key = lambda deadl: deadl.deadline)
        now = datetime.now()
        for t in tasks:
            cnt = 0
            for d in deadline:
                if t.deadline <= now + d and (t.last_notifier is None or t.last_notifier < d.total_seconds()//60) and cnt == 0:
                    self.send_notification(t)
                    t.last_notifier = int(d.total_seconds()//60)
                    self.session.commit()
                    cnt += 1


if __name__ == "__main__":
    notifier = Notifier()
    notifier.run()
