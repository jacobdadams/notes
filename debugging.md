# Debugging Tips for VSCode

## Debugging A Package

If you're using our python repo, your code is meant to be installed as a package with several different modules (ie, individual `something.py` files). Usually there's a `main.py` module that holds the main entry point for your program, and `setup.py`'s `entry_points` directs you to this via `package_name.module_name:method_name`.

With this packaging scheme, from within any of your python modules (individual `.py` files) you import from another module using `from . import module_name`. This works because it's been pip-installed as a package, which loads the package into the namespace as the parent.

However, if you try to use the standard VSCode "Python: Current File" debug config, these relative imports fail because it's just running that one lone file. It doesn't load the package into the namespace, thus there is no parent set (this is the same thing that happens in a Google Cloud Function, btw).

You can solve this by creating a new launch config in `launch.json` using the `module` directive instead of the `program` directive. There may be a better way of formatting the module name to make it more portable, but here it is hardcoded in, much like the `setup.py` entry point:

```json
{
    "name": "Python: pip installed module",
    "type": "python",
    "request": "launch",
    "module": "package_name.module_name",
    "console": "integratedTerminal",
    "justMyCode": true
}
```
