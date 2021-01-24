from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

from phonenumber_field.modelfields import PhoneNumberField


# class TimeZone(models.IntegerChoices):
#     FIRST = 1
#     SECOND = 2


class User(AbstractUser):
    phone = PhoneNumberField(
        verbose_name='phone', unique=True,
        error_messages={'unique': "Пользователь с таким номером телефона уже существует."},
    )
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'city', 'partner']

    first_name = models.CharField('first name', max_length=150)
    last_name = models.CharField('last name', max_length=150)
    middle_name = models.CharField('middle name', max_length=150, blank=True)
    email = models.EmailField('email address')
    city = models.CharField('city', max_length=255)
    partner = models.CharField('partner', max_length=255)

    # time_zone = models.CharField(choices=TimeZone.choices, default=TimeZone.FIRST)

    username = models.CharField('username', max_length=255, null=True, blank=True, default=None)

    def __str__(self):
        return self.phone.as_e164


class Device(models.Model):
    type = models.CharField('type', max_length=128)
    sid = models.CharField('sid', max_length=128, default='qwe')
    user = models.ForeignKey(User, related_name='devices', on_delete=models.CASCADE)


class Broadcast(models.Model):
    link = models.URLField('link')


class Poll(models.Model):
    question = models.CharField('question', max_length=255)
    first_answer = models.CharField('first_answer', max_length=255)
    second_answer = models.CharField('second_answer', max_length=255)
    first_answer_percentage = models.PositiveSmallIntegerField(null=True, blank=True,
                                                        validators=[MinValueValidator(0), MaxValueValidator(100)])
    timer_seconds = models.SmallIntegerField(blank=True, default=120)
    users = models.ManyToManyField(User, through='app.Vote', related_name='polls')


class Vote(models.Model):
    poll = models.ForeignKey(Poll, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='votes', on_delete=models.SET_NULL, null=True)
    first_answer_win = models.BooleanField(default=True)


@receiver(post_save, sender=User)
def password_set(sender, instance, created, **__):
    if created:
        instance.set_password('password')
        instance.save()
