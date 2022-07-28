# Pytest Tips and Tricks

## When to mock and when to patch

You can replace bits of code and data structures by either passing a Mock directly or by patching code (which either implicitely creates a mock or uses one you explicitely create and pass via patch()).

### 3rd-party code: Patch

You'll usually patch 3rd-party code that you've imported into your code under test. If there's just a single function you need to patch, use `mocker.patch.object(module, 'function_name')` and pass in a mock function object. If you need to patch an entire object, use `mocker.patch('module.object')`.

If you need to set certain attributes of your mocked-out object, or access it later to test if it's been called a certain way, you can create a new Mock and pass it's reference to patch() using the `new=` argument.

For example, I need to mock out reading a csv into a dataframe in my code under test. The resulting dataframe can be empty, but it needs to be a dataframe:

```python
read_csv_mock = mocker.Mock()
read_csv_mock.return_value = pd.DataFrame()
mocker.patch.object(pd, 'read_csv', new=read_csv_mock)
```

As noted below, I can patch out the entire arcpy.da.UpdateCursor context manager object while controlling the resource it returns:

```python
cursor_mock = mocker.MagicMock()
cursor_mock.__iter__.return_value = [
    ['12345', '42', 123.45, '12/25/2021'],
    ['67890', '18', 67.89, '12/25/2021'],
]
context_manager_mock = mocker.MagicMock()
context_manager_mock.return_value.__enter__.return_value = cursor_mock
mocker.patch('arcpy.da.UpdateCursor', new=context_manager_mock)
```

#### Where to patch

The [unittest docs on where to patch](https://docs.python.org/3/library/unittest.mock.html#id6), provide this guidance on where to patch:

> patch() works by (temporarily) changing the object that a name points to with another one. There can be many names pointing to any individual object, so for patching to work you must ensure that you patch the name used by the system under test.
>
> The basic principle is that you patch where an object is looked up, which is not necessarily the same place as where it is defined.

This means you have to think about the namespace of the function you're testing when it runs, which is not neccesarily the same as its file/package structure.

For example, in developing palletjack 3.0.0, I have the following module structure:

```
src\
    loaders.py
    transform.py
    updaters.py
    utils.py
__init__.py
```

In it's `__init__.py`, I have `from . import transform` along with several `from updaters import SomeClass` so that a client can `import palletjack` and then access the methods in transform via `palletjack.transform.method` and also directly import the classes via `from palletjack import SomeClass` (this may change...).

In `transform.py`, I have `from . import utils` so that I can access the utility methods. Because `utils` is not imported in `__init__.py`, these utility methods are not exposed to clients. `transform.py` looks something like this:

```python
from . import utils

class SomeTransformClass:
    def some_transform_method_that_calls_util_method(self):
        ...
        some_util_method()
        ...
```

Let's say I want to test `some_transform_method_that_calls_util_method` and I need to patch that utility method. Because the method under test only uses a single `utils` function, I'm just going to patch out that entire module. My first inclination is to patch it out _where it's defined_ like thus:

```python
import palletjack

mocker.patch.object(palletjack, 'utils', autospec=True)  #: autospec=True means it automatically stubs out all the functions in the object we're patching so we can check if it was called in the assert stage
transform_object = SomeClass()
transform_object.some_transform_method_that_calls_util_method()

palletjack.utils.some_util_method.assert_called_once()  #: make sure the util method was called
```

However, this doesn't work properly. Instead, we need to patch it out _where it's looked up_:

```python
import palletjack

mocker.patch.object(palletjack.transform, 'utils', autospec=True)  #: autospec=True means it automatically stubs out all the functions in the object we're patching so we can check if it was called in the assert stage
transform_object = SomeClass()
transform_object.some_transform_method_that_calls_util_method()

palletjack.transform.utils.some_util_method.assert_called_once()  #: make sure the util method was called
```

What's going on? `utils.py` is side-by-side with `transform.py` in the module hierarchy, not part of it somehow. Let's dig into the namspaces.

If you debug the first test and pause before you go into the method under test, you'll see that while `palletjack.utils` references a mock object with all the right mocked-out methods, when you continue the `some_transform_method_that_calls_util_method` call doesn't call the mocked-out `some_util_method`. This is because of the way `transform.py` imports `utils` into the namespace.

First, in our test `import palletjack` imports palletjack and all its contents (as defined in `__init__.py`) into the global namespace. So, in our test, if we were to try to directly call `util.some_util_method()`, it would reference our patched-out method.

However, we instead call the utility method in `transform.py`. By calling `from . import utils` in `transform.py`, it imports the `utils` module and its functions into its namespace, but if you're still debugging the test you'll see that the contents of the "globals" namespace have changed as we get into the method under test. There is no `palletjack.utils`, but there is a `utils` with the regular, non-patched methods. The method under test does not have any reference to `palletjack.utils` so our patch is not visibile to it.

Going back to the test module's perspective, the `utils` referenced in the method under test has a full reference of `palletjack.transform.utils`. Thus, in the test module, we need to patch that out instead of `palletjack.utils`, as shown in the second example above. This is what is meant by patching where it is called instead of where it is defined.

#### Patching objects vs functions

For `mocker.patch.object()`, if the function you're patching needs to return another object and you want to set the return value for a method of that new object, you have to set the method's return value on `method_mock.return_value.method_name.return_value`.

For example, in previous tests I needed to just patch out `feature_layer = arcgis.features.FeatureLayer.fromitem()` so that it didn't make a call. The tests never relied on feature_layer , so I didn't need a `new=` value in my patch:

```python
mocker.patch.object(arcgis.features.FeatureLayer, 'fromitem')
```

However, for another test I needed to set the return value of `feature_layer.edit_features()`. I initially tried creating a mock with a property `.edit_features` and set `.edit_features.return_value` to the desired output. I then passed this to the `new=` parameter of `mocker.patch.object`. However, this fails because we are patching a function, so the mock that is used for patching is the function object, NOT the return value of that function (remembering that everything in Python is an object, including functions). Therefore, my mock's `.edit_features.return_value` property is never accessed.

Instead, I need to set `.return_value.edit_features.return_value` to the desired output. This means "patch this function with a mock object. The mock object's return value (another mock) should have the `.edit_features()` method, and this method's return value should be this set of data:".

```python
#: This is the mocked function object
fromitem_function_mock = mocker.Mock()
#: This is the return value of the .edit_features method of the object returned by the mocked function object
fromitem_function_mock.return_value.edit_features.return_value = {
    'addResults': [],
    'updateResults': [
        {
            'objectId': 1,
            'success': True
        },
        {
            'objectId': 2,
            'success': True
        },
    ],
    'deleteResults': [],
}
#: Patch the fromitem() method on the arcgis.features.FeatureLayer object with our function mock
mocker.patch.object(arcgis.features.FeatureLayer, 'fromitem', new=fromitem_function_mock)
```

#### patch vs patch.object

From [stackexchange](https://stackoverflow.com/a/18393879/16290428):
"Patch assumes that you are not directly importing the object but that it is being used by the object you are testing"
"If you are directly importing the module to be tested, you can use patch.object as follows:"

```python
#test_case_2.py
import foo
from mock import patch

@patch.object(foo, 'some_fn')
def test_foo(test_some_fn):
    test_some_fn.return_value = 'test-val-1'
    tmp = foo.Foo()
    assert tmp.method_1() == 'test-val-1'
    test_some_fn.return_value = 'test-val-2'
    assert tmp.method_1() == 'test-val-2'
```

### Your code with classes: usually Mock()

Let's say you've got a class with methods and you want to test the methods. How do you deal with `self`? There are two options.

**Option 1**: If `__init__()` is minimal and the function under test doesn't rely on other functions changing the object's attributes, just go ahead and instantiate a new object and test the method directly.

**Option 2**: If `__init__()` is complex and/or there are other things that need to happen to get the object in the right state for testing, create a mock for the object and set it's desired state manually. Then, call the method under test through the class definition instead of the object. This mock doesn't need to have all the object's attributes or methods, just the ones that are required for the code under test.

This works because `instance.method()` is syntactic sugar for `module.class.method(instance)`— that's why we always have `self` as the first parameter in instance methods. We create a mock in place of the instance and pass it to the method.

For example, I want to test the `download_sftp_files` method in the `SFTPLoader` class from the `data_coupler` module. This method is not static but relies on several different `self.` references:

```python
#: Set up the mock instance of our class
sftploader_mock = mocker.Mock()
sftploader_mock.secrets.KNOWNHOSTS = 'knownhosts_file'
sftploader_mock.secrets.SFTP_HOST = 'sftp_host'
sftploader_mock.secrets.SFTP_USERNAME = 'username'
sftploader_mock.secrets.SFTP_PASSWORD = 'password'
download_dir_mock = mocker.Mock()
download_dir_mock.iterdir.side_effect = [[], ['file_a', 'file_b']]
sftploader_mock.download_dir = download_dir_mock

...

#: Call our method under test via the class instead of the instance:
data_coupler.SFTPLoader.download_sftp_files(sftploader_mock)

#: Test the resulting state of the mocked object
```

## Specific tasks, mocks, etc

### Context Managers

You can mock out a context manager by first creating a Mock for the resource the manager returns. Then, create a Mock for the manager itself and set it's `.return_value.__enter__.return_value` to the resource mock. Finally, patch the context manager with the manager mock:

```python
connection_mock = mocker.MagicMock()
context_manager_mock = mocker.MagicMock()
context_manager_mock.return_value.__enter__.return_value = connection_mock
mocker.patch('pysftp.Connection', new=context_manager_mock)
```

### Iterable

You can mock an iterable by creating a mock and setting it's `.__iter__.returnvalue` to a list or other iterable with your desired values:

```python
cursor_mock = mocker.MagicMock()
cursor_mock.__iter__.return_value = [
    ['12345', '42', 123.45, '12/25/2021'],
    ['67890', '18', 67.89, '12/25/2021'],
]
```

### arcpy.da cursors

You can combine context manager and iterable mocking to mock out arcpy.da cursors:

```python
cursor_mock = mocker.MagicMock()
cursor_mock.__iter__.return_value = [
    ['12345', '42', 123.45, '12/25/2021'],
    ['67890', '18', 67.89, '12/25/2021'],
]
context_manager_mock = mocker.MagicMock()
context_manager_mock.return_value.__enter__.return_value = cursor_mock
mocker.patch('arcpy.da.UpdateCursor', new=context_manager_mock)

...

cursor_mock.updateRow.assert_called_with(['12345', '57', 100.00, '1/1/2022'])
```

### Patching out ALL of arcpy

Sometimes you have tests that patch out methods in arcpy (like the cursor example above) that you want to work on environments where arcpy is not available (a conda env without arcpy, github's CI/CD testing, etc), or they may otherwise rely on arcpy being present (an overly broad import in a module). To do this, you can create a mock arcpy object and insert that into `sys.modules` as `arcpy`. Now, in your tests, the `arcpy` name is bound to your mock instead of the real module. If arcpy already exists in your test's namespace, it stomps over the normal arcpy name. If a subsequent import tries to import arcpy, then they get the mock object instead.

To do this, create a module _in your test folder_ named something like `mock_arcpy.py` and put the following code in it:

```python
import sys
from unittest.mock import Mock

module_name = 'arcpy'
arcpy = Mock(name=module_name)
sys.modules[module_name] = arcpy

```

This inserts a mock into the namespace called `arcpy`. Now, in your test file, just `import mock_arcpy` to insert this fake arcpy into your test's namespace. Any calls to `arcpy` will get your mock arcpy module and thus automatically create mock modules/classes/methods as needed.

As a bonus, your tests won't import the real arcpy (which takes forever) and thus may run significantly faster.

### Different return values each time

If you have a function that is called multiple times in your function under test and you need to return different values each time, you can use `.side_effect` with an iterable and it will iterate through it each time the function is called:

```python
download_dir_mock = mocker.Mock()
download_dir_mock.iterdir.side_effect = [[], ['file_a', 'file_b']]

#: In function under test, the download_dir's .iterdir() method is called twice. The first time it returns the empty
#: list, the second time it returns the list ['file_a', 'file_b']
```

### Passing an attribute to and through a mocked object

Note: there may be other/better ways of doing this. This was a first try.

Also note: this may be a symptom of an overly-ambitious test, function, or both. Could be refactor time.

If your code under test uses an object with an attribute set by the initializer, your code generates the argument, the object is passed to the code you are able to mock for testing, and you want to test that the attribute is set correctly, you can use a lambda function that just returns the value directly. You have to make sure the lambda's variable name matches the methods.

For example, I want to test that my pysftp connection is opened using the right values. One parameter is the connections options object that holds the knownhosts path as returned by pysftp.CnOpts(). My code generates this argument based on other input, so I can't hardcode it into the test. I can mock this object to have whatever value is passed in by my code under test with the following:

```python
cnopts_mock = mocker.Mock()
cnopts_mock.side_effect = lambda knownhosts: knownhosts  #: knownhosts is the argument name to the initializer
mocker.patch('pysftp.CnOpts', new=cnopts_mock)
```

### Force an ImportError for an available package

Say you want to test your code properly handles a missing import, but your test environment has it installed/availble (like above where you're mocking out all of arcpy, so `arcpy` exists in your namespace but you want to test that your code properly warns the user that it isn't, in fact, installed).

You can use a pytest fixture that wraps the `__import__` builtin with a small function that manually raises an `ImportError` for defined package names:

```python
@pytest.fixture
def hide_available_pkg(monkeypatch):
    """Mocks import to throw an ImportError (for error handling testing purposes) for a package that does, in fact, exist"""
    import_orig = builtins.__import__

    def mocked_import(name, *args, **kwargs):
        if name == 'arcpy':
            raise ImportError()
        return import_orig(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', mocked_import)
```

We specifically call out the package name in the `if name ==` line in `mocked_import()` and raise our error if that's the name it's trying to import. Otherwise, we just pass everything to the normal import function.

To use this, we just decorate our test function thusly:

```python
@pytest.mark.usefixtures('hide_available_pkg')
def test_my_method_raises_error_on_import_failure():
    ...
```

### Mock out calls to open

If you're using `open()` as a context manager, it's a little tricky to mock and assert. First, you need to create a mock with the `mock_open()` function and then patch out the builtin `open`:

```python
open_mock = mocker.mock_open()
mocker.patch('builtins.open', open_mock)
```

If you're using `open` to read data, you can pass the `read_data` parameter to `mock_open()` to define what should come back.

If you're writing and want to assert what was written, you have to jump through some hoops to assert. First, you call the `open_mock` object that was created from `mock_open()`. Then, you can access the `.write.call_arg_list` (and other normal call assertions) from that. You may need to debug to make sure you've got the expected values right. In the example below, there was a lot of additional calls for some reason (unknown for now). And then, each call was actually a "call" object with a list of tuples. I had to get the first two write calls, the first tuple in the list for each, and then compare against a single-item tuple of the expected write.

```python
#: I'm testing whether the middle empty `b''` is skipped in the write calls within _save_response_content(), which
#: iterates over the return from .iter_content and passes if the chunk is False
def test_save_response_content_skips_empty_chunks(self, mocker):
    response_mock = mocker.MagicMock()
    response_mock.iter_content.return_value = [b'\x01', b'', b'\x02']

    open_mock = mocker.mock_open()
    mocker.patch('builtins.open', open_mock)

    palletjack.loaders.GoogleDriveDownloader._save_response_content(response_mock, '/foo/bar', chunk_size=1)

    assert open_mock().write.call_args_list[0][0] == (b'\x01',)
    assert open_mock().write.call_args_list[1][0] == (b'\x02',)
```

References:
[https://docs.python.org/3/library/unittest.mock.html#mock-open](https://docs.python.org/3/library/unittest.mock.html#mock-open)

### Asserting args

You can use `assert_called_with`, `assert_called_once_with`, and `assert_any_call` to test that a method/function was called as expected. However, you may need to specify any keyword args using arg_name=value in the assert call to get the test to pass as expected:

```python
session_mock.return_value.get.assert_called_with(
    'https://docs.google.com/uc?export=download', params={'id': 'foo_file_id'}, stream=True
)
```
