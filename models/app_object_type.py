"""
Meta class to customize what is returned by calling type() on one of the backend model
objects (User, Datespot, Match).

Goal is to simplify testing and prevent tests erroneously failing because of different
class module names in different execution contexts.

See https://stackoverflow.com/questions/56879033/how-do-i-override-type-method-in-python-object
"""

class DatespotAppType(type):
    def __repr__(self):
        return self.__name__ + "Obj"