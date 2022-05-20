# -*- coding: utf-8 -*-
"""
Secrets factory.
"""

# Standard imports
import logging
from abc import (
    ABC,
    abstractmethod,
)
from collections import OrderedDict
from inspect import getdoc


logger = logging.getLogger(__name__)


# pylint: disable=missing-function-docstring


class SecretFactory:
    """
    Factory class for generating secrets.
    """

    class_map = {}

    # def _get_secret_class(self, class_name):
    #     """
    #     Return secret class.
    #     """
    #     secret_class = self.class_map.get('class_name')
    #     if not secret_class:
    #         raise SecretTypeNotFoundError(class_name)
    #     return secret_class

    @classmethod
    def register_handler(cls, secret_type):
        def wrapper(secret_class):
            cls.class_map[secret_type] = secret_class
            return secret_class
        return wrapper

    @classmethod
    def get_handler(cls, secret_type):
        return cls.class_map[secret_type]()

    @classmethod
    def add_parser_arguments(cls, parser):
        for secret_class in cls.class_map.values():
            secret_class().add_parser_arguments(parser)
        return parser


class SecretHandler(ABC):
    """
    Abstract secrets class.
    """
    @abstractmethod
    def generate_secret(self, secret_type, **kwargs):
        raise NotImplementedError

    def add_parser_arguments(self, parser):
        """
        Override this method with argparse arguments specific
        to the secret type as necessary.
        """
        return parser

    def is_generable(self):
        try:
            self.generate_secret(None)
        except NotImplementedError:
            return False
        else:
            pass
        return True

    def describe(self):
        return OrderedDict(
            {
                'type': getattr(self, 'type'),
                'description': getdoc(self),
                'generable': self.is_generable()
            }
        )


# vim: set ts=4 sw=4 tw=0 et :
