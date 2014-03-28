#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ServiceRequest(object):
    """
    This class is an abstract class created to serve a single request.

    The object handles the request for the *path* given on the *service*.
    *service* is an instance of
    :class:`napixd.services.collection.CollectionService`.
    """

    def __init__(self, context, path):
        self.context = context
        self.service = context.service
        # Parse the url components
        self.path = list(path)
        self.lock = self.service.lock

    def check_datas(self):
        """
        Filter and check the collection fields.

        Remove any field that is not in the collection's field
        Call the validator of the collection
        """
        return {}

    def get_manager(self, path=None):
        """
        Retreive the manager associated with the current request
        """
        manager = self.context.get_manager_instance(self.path if path is None else path)
        return manager

    def call(self):
        """
        Make the actual call of the method
        """
        raise NotImplementedError

    def make_url(self, result):
        """
        Creates an url for the *list* **result**.
        """
        path = list(self.path)
        path.append(result)

        return self.service.resource_url.reverse(path)

    def get_callback(self):
        raise NotImplementedError

    def handle(self):
        lock = self.lock.acquire() if self.lock else None

        try:
            # obtient l'object designé
            self.manager = self.get_manager()

            # recupère la vue qui va effectuer la requete
            self.callback = self.get_callback()
            # recupère les données valides pour cet objet
            self.data = self.check_datas()
            # recupere les arguments a passer a cette vue
            result = self.call()
            return result
        finally:
            if lock is not None:
                lock.release()
