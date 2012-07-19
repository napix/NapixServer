#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.db import models


class Car(models.Model):
    name = models.CharField( max_length=200, help_text='name of the var')
    owner = models.CharField( max_length=200, blank=True)
    max_speed = models.IntegerField( default=0, help_text='Maximum speed')
    created = models.DateField( auto_now_add=True)

    class Meta:
        db_table = 'car'

class Parent( models.Model):
    name = models.CharField( max_length=200)

    class Meta:
        db_table = 'parent'

class Child( models.Model):
    father = models.ForeignKey( Parent, related_name='children')
    name = models.CharField( max_length=200)

    class Meta:
        db_table = 'child'
