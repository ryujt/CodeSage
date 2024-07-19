# JobFlow Diagram

## JobFlow Description

Job-Flow is a diagram that illustrates how an event occurring in one object affects other objects.

### When an OnClick event occurs in object A and it calls the Method of object B
A.OnClick --> B.Method

### Returning the result after executing the Method Case 1
A.OnClick --> B.Method
B.Method.ReturnValue --> A.HandleResponse

### Returning the result after executing the Method Case 2
A.OnClick --> B.Method
B.Method.ReturnValue --> C.HandleResponse

### Calling different methods based on the result of the Method execution
A.OnEvent --> B.Method
B.Method.false --> A.HandleFalse
B.Method.true --> A.HandleTrue

## JobFlow Components
* master is the name of the core object.
* Object lists the names of objects included in the Job-Flow.

## JobFlow Script Example

``` jobflow
master: MasterObject
Object: MasterObject, ObjectA, ObjectB, ObjectC

ObjectA.OnEvent1 --> ObjectB.Method1

ObjectA.OnEvent2 --> ObjectB.Method2
ObjectB.Method2.result --> ObjectA.HandleResponse

ObjectA.OnEvent3 --> ObjectB.Method3
ObjectB.Method3.true --> ObjectA.HandleTrue
ObjectB.Method3.false --> ObjectA.HandleFalse

ObjectA.OnEvent4 --> ObjectB.Method4
ObjectB.Method4 --> ObjectC.Method4

ObjectC.PublicMethod --> ObjectC.PrivateMethod
```

## JobFlow Code Conversion Example

``` csharp
class ObjectA
{
    public event EventHandler OnEvent1;
    public event EventHandler OnEvent2;
    public event EventHandler OnEvent3;
    public event EventHandler OnEvent4;
    public void HandleResponse()
    {
    }
    public void HandleTrue()
    {
    }
    public void HandleFalse()
    {
    }
}

class ObjectB
{
    public void Method1()
    {
    }
    public void Method2()
    {
    }
    public void Method3()
    {
    }
    public void Method4()
    {
    }
}

class ObjectC
{
    public void Method4()
    {
    }
    public void PublicMethod()
    {
        PrivateMethod();
    }
    public void PrivateMethod()
    {
    }
}

class MasterObject
{
    public MasterObject()
    {
        _objectA.OnEvent1 += (sender, e) =>
        {
            _objectB.Method1();
        };
        _objectA.OnEvent2 += (sender, e) =>
        {
            var result = _objectB.Method2();
            _objectA.HandleResponse(result);
        };
        _objectA.OnEvent3 += (sender, e) =>
        {
            var result = _objectB.Method3();
            if (result)
            {
                _objectA.HandleTrue();
            }
            else
            {
                _objectA.HandleFalse();
            }
        };
        _objectA.OnEvent4 += (sender, e) =>
        {
            _objectB.Method4();
        };
    }
    private ObjectA _objectA;
    private ObjectB _objectB;
    private ObjectC _objectC;
}
```