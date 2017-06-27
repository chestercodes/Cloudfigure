## Cloudfigure ##

The goals of this are to be able to retrieve configuration from cloudformation stack outputs.

The code must be able to do the following:

- Get values from stacks from being pointed to the output Logical name
- get values from outputs of child stacks by being pointed to the `LogicalNameOfChildStack.LogicalNameOfChildStackOutput`
- Get values from stack outputs into python dictionary 
- Substitute values into file on local drive.
- Unencrypt values using KMS.
- optionally STS assume role to retrieve stacks and unencrypt 
- be configured in json structure which spans different technologies.
- retrieve stack config using StackId specified in either:
 - call to python script
 - json file specified on hard disk/s3 in call to python script



Examples of config json:

``` javascript
{
    'AssumeRole': '',
     'Configuration': [
        {}
    ]
} 
```