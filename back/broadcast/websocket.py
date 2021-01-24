import os
import socketio

from urllib.parse import parse_qs
from django.core.wsgi import get_wsgi_application
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from app.models import Device, Broadcast, Poll, Vote

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broadcast.settings')

sio = socketio.Server(logger=True)
application = socketio.WSGIApp(sio, get_wsgi_application())

Device.objects.all().delete()


@sio.event
def connect(sid, environ):
    print(f'connected: {sid=}')
    query = parse_qs(environ['QUERY_STRING'])
    token = query.get('token')[0]
    user = Token.objects.get(key=token).user
    device_type = query.get('type')[0]
    Device.objects.create(type=device_type, user=user, sid=sid)
    sio.emit(token, dict(
        payload=dict(
            devices=list(user.devices.all().values_list('type', flat=True)),
        ),
        type='connection'
    ))
    if broadcast := Broadcast.objects.last():
        sio.emit(token, dict(
            payload=dict(
                link=broadcast.link,
            ),
            type='broadcast_start'
        ))


@sio.event
def disconnect(sid):
    print(f'disconnected: {sid=}')
    device = Device.objects.get(sid=sid)
    user = device.user
    if not hasattr(user, 'auth_token'):
        user.devices.all().delete()
        sio.emit(user.phone, dict(
            payload=dict(
                devices=[],
            ),
            type='disconnection'
        ))
    else:
        device.delete()
        sio.emit(str(user.auth_token), dict(
            payload=dict(
                devices=list(user.devices.all().values_list('type', flat=True)),
            ),
            type='disconnection'
        ))


@sio.event
def vote(sid, data):
    device = Device.objects.get(sid=sid)
    user = device.user
    data = data['payload']
    Vote.objects.get_or_create(user=user, poll_id=data['id'], first_answer_win=True if data['answer'] == 1 else False)


@receiver(post_save, sender=Broadcast)
def broadcast_start(sender, instance, created, **__):
    sio.send(dict(
        payload=dict(
            link=instance.link,
        ),
        type='broadcast_start'
    ))


@receiver(post_delete, sender=Broadcast)
def broadcast_end(sender, instance, **__):
    if not sender.objects.exists():
        sio.send(dict(
            payload=dict(),
            type='broadcast_end'
        ))


def get_poll_percent(poll):
    return int(poll.votes.filter(first_answer_win=True).count() / poll.votes.count() * 100)


@receiver(post_save, sender=Poll)
def poll_start(sender, instance, created, **__):
    sio.send(dict(
        payload=dict(
            question=instance.question,
            first_answer=instance.first_answer,
            second_answer=instance.second_answer,
            timer_seconds=instance.timer_seconds,
            id=instance.id
        ),
        type='poll_start'
    ))
    sio.sleep(instance.timer_seconds)
    print('waited')
    first_answer_percentage = instance.first_answer_percentage or get_poll_percent(instance)
    sio.send(dict(
        payload=dict(
            question=instance.question,
            first_answer=instance.first_answer,
            first_answer_percent=first_answer_percentage,
            second_answer=instance.second_answer,
            second_answer_percent=100 - first_answer_percentage,
            id=instance.id,
        ),
        type='poll_results'
    ))


@receiver(pre_delete, sender=Poll)
def poll_end(sender, instance, **__):
    if not sender.objects.exists():
        sio.send(dict(
            payload=dict(
                winner=1 if instance.first_answer_percentage > 50 else 2
            ),
            type='poll_end'
        ))
