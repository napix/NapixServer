#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
import operator


class Company(models.Model):
    name = models.CharField( max_length=1000)
    address = models.TextField()

class Invoice(models.Model):
    company = models.ForeignKey( Company)
    serial_number = models.IntegerField()
    client_name = models.CharField( max_length=1000)
    client_address = models.TextField()
    created = models.DateField( auto_now_add=True)

    def save( self, *args, **kw):
        if not self.number:
            self.number = ( self.__class__.filter(
                created__year = self.created.year, created__month = self.created.month
                ).aggregate(x=Max('number')).get( 'x') or 0 ) + 1
        return super( Invoice, self).save(*args, **kw)

    @property
    def number( self):
        return '{0}{1:02i}-{2}'.format(
                self.created.year, s.created.month, self.serial_number)

    @property
    def all_products(self):
        return self.product_set.all()

    @property
    def total_sum( self ):
        return reduce( operator.add,
                map( operator.attrgetter( 'total'), self.all_products))

    @property
    def total_tax( self):
        return reduce( operator.add,
                map( operator.attrgetter( 'tax'), self.all_products))

    @property
    def total_sum_tax( self ):
        return self.total_sum + self.total_tax

class Product(models.Model):
    DEFAULT_TAX = 0.196

    invoice = models.ForeignKey( Invoice )
    description = models.CharField( max_length = 250)
    reference = models.CharField( max_length = 250)
    price = models.FloatField()
    quantity = models.IntegerField( default = 1)
    tax_rate = models.IntegerField( default = DEFAULT_TAX )

    @property
    def tax(self):
        return self.total * self.tax_rate

    @property
    def total(self):
        return self.price * self.quantity

    @property
    def total_tax( self):
        return self.total + self.tax

