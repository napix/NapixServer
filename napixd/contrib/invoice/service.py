#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.connectors.django import DjangoModelManager, DjangoRelatedModelManager, DjangoImport

__all__ = ('CompanyManager', )

with DjangoImport():
    from napixd.contrib.invoice.models import Invoice, Company, Product


class CompanyManager(DjangoModelManager):
    name = 'company'
    model = Company
    managed_class = ['InvoiceManager']


class InvoiceManager(DjangoRelatedModelManager):
    name = 'invoices'
    model = Invoice
    related_to = 'Company'
    model_fields_exclude = ('serial_number', )
    managed_class = ['ProductManager']


class ProductManager(DjangoRelatedModelManager):
    name = 'products'
    model = Product
    related_to = 'Invoice'
