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
    def get_handler_classes(cls):
        return [
            secret_class for secret_class
            in cls.class_map.values()
        ]

    @classmethod
    def add_parser_arguments(cls, parser):
        for secret_class in cls.get_handler_classes():
            secret_class().add_parser_arguments(parser)
        return parser

    @classmethod
    def describe_secret_classes(cls):
        return [
            secret_class().describe()
            for secret_class in cls.get_handler_classes()
        ]


class SecretHandler(ABC):
    """
    Abstract secrets class.
    """
    @abstractmethod
    def generate_secret(self, **kwargs):
        raise NotImplementedError

    def add_parser_arguments(self, parser):
        """
        Override this method with argparse arguments specific
        to the secret type as necessary.
        """
        return parser

    def is_generable(self):
        result = None
        try:
            result = self.generate_secret()
        except NotImplementedError:
            return False
        except RuntimeError:
            return True
        return result not in ['', None]

    def describe(self):
        return OrderedDict(
            {
                'Type': self.__module__.split('.')[-1],
                'Description': getdoc(self),
                'Generable': self.is_generable()
            }
        )


# vim: set ts=4 sw=4 tw=0 et :
