## Job Flow Description

Job-Flow is a diagram that illustrates how an event occurring in one object affects other objects.

### When an OnClick event occurs in object A and it calls the Method of object B

A.OnClick --> B.Method

### Returning the result after executing the Method Case 1

A.OnClick --> B.Method  
B.Method.ReturnValue --> A.HandleResponse  

* When the OnClick event occurs in object A, B.Method is executed.  
* After executing B.Method, it returns a result as ReturnValue, which is passed to A.HandleResponse.  

### Returning the result after executing the Method Case 2

A.OnClick --> B.Method  
B.Method.ReturnValue --> C.HandleResponse  

### Calling different methods based on the result of the Method execution

A.OnEvent --> B.Method  
B.Method.false --> A.HandleFalse  
B.Method.true --> A.HandleTrue  

* When the OnEvent event occurs in object A, B.Method is executed.  
* After executing B.Method, if the result is false, A.HandleFalse is executed; if true, A.HandleTrue is executed.  

## Rules

### Job Flow Script Header

A Job Flow Diagram starts with a header.

* master: {name of the master object}  
* Object: {lists the names of objects}  

### Left & Right Sides

After the header, it consists of three parts in the format "Left --> Right".  
The Left and Right sides can use only the following three expressions:

* Object.Method  
* Object.Method.ReturnValue  
  * The return value that occurs after executing "Object.Method"  
* Object.Event  

### Return values can be expressed as follows:

* For a single return value:  
  * Object.Method.result  
* For a boolean return value:  
  * Object.Method.true  
  * Object.Method.false  
* For multiple types of return values:  
  * Object.Method.case1  
  * Object.Method.case2  
  * Object.Method.caseN  

## Job Flow Script Example

jobflow
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


Below is the code based on the Job Flow Script above.  
It demonstrates how the Job Flow is converted into actual code.

csharp
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