# Pytest Tips and Tricks

## When to mock and when to patch

You can replace bits of code and data structures by either passing a Mock directly or by patching code (which either implicitely creates a mock or uses one you explicitely create and pass via patch()).

### 3rd-party code: Patch

You'll usually patch 3rd-party code that you've imported into your code under test. If there's just a single function you need to patch, use `mocker.patch.object(module, 'function_name')`. If you need to patch an entire object, use `mocker.patch('module.object')`. 

If you need to set certain attributes of your mocked-out object, or access it later to test if it's been called a certain way, you can create a new Mock and pass it's reference to patch() using the `new=` argument.

For example, I need to mock out reading a csv into a dataframe in my code under test. The resulting dataframe can be empty, but it needs to be a dataframe:

```python
read_csv_mock = mocker.Mock()
read_csv_mock.return_value = pd.DataFrame()
mocker.patch.object(pd, 'read_csv', new=read_csv_mock)
```

As noted above, I can patch out the entire arcpy.da.UpdateCursor context manager object while controlling the resource it returns:

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
