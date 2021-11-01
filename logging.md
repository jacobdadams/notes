# Python Logging

## Logging structure

re https://stackoverflow.com/questions/42388844/where-to-configure-logging:

Author should instantiate the logger at the right level:

Package logger should go in the packages `__init__` file. Note the use of `__name__`, it'll resolve to SomePackage:
```python
import logging
package_logger = logging.getLogger(__name__)
```

Module logger at the top of your module. Note the power of `__name__`! Here it'll resolve to SomePackage.SomeModule.
```python
import logging
module_logger = logging.getLogger(__name__)
```

Class level logger could go in a classes `__init__` (or use a meta-class). Note the awesome power of `__name__` enhanced with getLogger! The loggers name will be SomePackage.SomeModule.SomeClass. Also, not the underscore in _class_logger to signal that it is for internal use.:
```python
class SomeClass:
    def __init__(self):
        self._class_logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
```

Instance logger in the classes `__init__`. Use ID to produce a unique identifier. Note the stupend... you get the idea. Logger name will be SomePackage.SomeModule.SomeClass.<large_unique_number>:
```python
class SomeClass:
    def __init__(self):
        self._instance_logger = logging.getLogger(__name__).getChild(self.__class__.__name__).getChild(id(self))
```

The names may not suit your application. For instance you may want an instance logger that is derived from one of it's instantiating args. However, you should still aim to get a grip on your logger at the right level.

---

THEREFORE, let's lay out a package structure (matches github.com/agrc/python):

```
my_project/
 - src/
   - my_project/
     - __init__.py
     - main.py
     - other_module.py
       - class Class1
       - class Class2
 - tests/
 - setup.py
```

Now let's work our way from down the hierarchy to create child loggers that inherit their ancestor's levels, formatters, etc. 

my_project is both the name of the folder/repo and the package. This seems to be a common pattern but not necessary (and sometimes confusing).

main.py is our main module for the program, not to be confused with `'__main__'`. This is where we'll do our cli and use clasess from other_module by first calling `import .other_module`. It will have some function defined that is the entry point specified in setup.py and is probably also called from `if __name__ == '__main__':`. 

other_module.py holds two helper classes, Class1 and Class2. 

### Package logger

`my_project/__init__.py` is run first whenever the package is imported, which I think occurs whenever it's run using an entry point defined in setup.py. Therefore, it's a great place to put stuff that should be package-wide- like the package's main logger! Let's set up a logger to log debug and above to the console. Any children of this logger will inherit it's level, etc.

```python
logger = logging.getLogger('__name__')
logger.setLevel(logging.DEBUG)
cli_handler = logging.StreamHandler(sys.stdout)
cli_handler.setLevel(logging.DEBUG)
cli_formatter = logging.Formatter(
    fmt='%(levelname)-7s %(asctime)s %(module)10s:%(lineno)5s %(message)s', datefmt='%m-%d %H:%M:%S'
)
cli_handler.setFormatter(cli_formatter)
logger.addHandler(cli_handler)
```

If we were to look at the running code's `logging.Logger.manager.loggerDict` ([https://stackoverflow.com/a/62585966/16290428](https://stackoverflow.com/a/62585966/16290428)), this logger would be named `my_project`.

#### Alternate

The code in `__init__.py` is run ANY time it's imported, which includes everytime you save the file in VS Code (and probably some other dev-related times too). This can cause unplanned file rotation if you've got a rotating file handler.

Calls to our loggers in each module/class go to the proper logger in the hierarchy because we use the loggers we got via `__name__`. If we don't want to put something in `__init__.py`, we could just as easily call `project_logger = .getLogger('my_project')` in the main.py module. Now, `project_logger` would be have the hierarchical name `my_project` and any other loggers in the my_project package created with `__name__` would be children (because `__name__` resolves to package.module, so my_project.other_module).

### Module loggers

Now we need to set up loggers for the modules. By default, they will be children of the package's logger (citation needed?). We'll do this at the beginning of the both main.py and other_module.py, after the imports but before any functions (or maybe within `if __name__ == '__main__' in main.py).

```python
module_logger = logging.getLogger(__name__)
```

These loggers will be named `my_project.main` and `my_project.other_module`. We can use them via `module_logger.info()` (or whatever other level).

### Class loggers

In Class1 and Class2, we can create class loggers within each classes' `__init__()` as follows:

```python
    def __init__(self):
        self._class_logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
```

These loggers will be named `my_project.other_module.Class1` and `my_project.other_module.Class2`. We use them via `self._class_logger.info()`.

## Setting levels, handlers, etc

Because all the other loggers are children of the `my_project` logger, they inherit it's level, handler, and formatter. If we want to make changes to that, we'll do it in `__init__.py`.  Generally, classes and other modules shouldn't try to specify other levels or handlers (unless it's a logger that's not part of the hierarchy, like a rotating file handler logger used for writing out some other file). Do it in one place and keep it clean.

## Accessing imported code's loggers

Let's say you've imported a library that uses loggers, possibly using this same heirarchy. Usually, a library shouldn't define any handlers/formatters, just creating the loggers. Then, in your code, you can handle it however you'd like. The libary should document the names of the loggers it creates. In your code, you can then get these loggers by name and attach whatever handlers/formatters you've already created to them. You must do this manually; I'm not seeing any way to attach the library's loggers as children of your app's loggers (ie, `app.library.module.class`). However, as long as they're using the same handler, messages created by the loggers will be added in the appropriate place/order/format.
