## Cloudfigure ##

The goals of this are to be able to retrieve configuration from cloudformation stack outputs.

The code must be able to do the following:

- be called as a script or imported and used as a module
- Get values from stacks from being pointed to the output Logical name
- get values from outputs of child stacks by being pointed to the `LogicalNameOfChildStack.LogicalNameOfChildStackOutput`
- Get values from stack outputs into python dictionary 
- optionally substitute values into file on local drive. using templating like #{ConfigurationValue}
- Unencrypt base64 encoded values using KMS. 
- optionally STS assume role to retrieve stacks and unencrypt 
- be configured in json structure in a file which the name defaults to Cloudfigure.json.
- retrieve stack config using StackId specified in either:
 - call to python script
 - json file specified on hard disk/s3 in call to python script



Example of Cloudfigure.json:

``` javascript
{
    'Configuration': [      
            {'Name': 'SomeAddress', 'Location': 'SomeEndpoint'},
            {'Name': 'SomePassword', 'Location': 'SomeOutputName', 'Unencrypt': true},
            {'Name': 'SomeChildValue', 'Location': 'SomeChildStack.SomeOutputName'},
            {'Name': 'SomeChildPassword', 'Location': 'SomeChildStack.SomeOutputName', 'Unencrypt': true}      
    ],
    'SubstituteInto': './SomePath.txt'
} 
```

