from app.celery_app import celery_app
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'close-expired-auctions': {
        'task': 'close_expired_auctions',
        'schedule': crontab(minute='*/1'),
    },
    'activate-scheduled-auctions': {
        'task': 'activate_scheduled_auctions',
        'schedule': crontab(minute='*/1'),
    },
}

if __name__ == '__main__':
    celery_app.start()
