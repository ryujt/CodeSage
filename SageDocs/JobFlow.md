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

## Rules

### JobFlow Script Header

A JobFlow Diagram starts with a header.

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