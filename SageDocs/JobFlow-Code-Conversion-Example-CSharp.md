# JobFlow Code Conversion Example CSharp

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

    public void HandleResponse(int data)
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

    public int Method2()
    {
    }

    public bool Method3()
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