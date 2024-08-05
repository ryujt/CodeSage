# JobFlow Code Conversion Example Go

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

``` go
package MasterObject

import "fmt"

type ObjectA struct {
    onEvent1       func()
    onEvent2       func()
    onEvent3       func()
    onEvent4       func()
    handleResponse func(int)
    handleTrue     func()
    handleFalse    func()
}

func (a *ObjectA) HandleResponse(data int) {
    if a.handleResponse != nil {
        a.handleResponse(data)
    }
}

func (a *ObjectA) HandleTrue() {
    if a.handleTrue != nil {
        a.handleTrue()
    }
}

func (a *ObjectA) HandleFalse() {
    if a.handleFalse != nil {
        a.handleFalse()
    }
}

type ObjectB struct{}

func (b *ObjectB) Method1() {
    fmt.Println("ObjectB Method1 called")
}

func (b *ObjectB) Method2() int {
    fmt.Println("ObjectB Method2 called")
    return 0
}

func (b *ObjectB) Method3() bool {
    fmt.Println("ObjectB Method3 called")
    return true
}

func (b *ObjectB) Method4() {
    fmt.Println("ObjectB Method4 called")
}

type ObjectC struct{}

func (c *ObjectC) Method4() {
    fmt.Println("ObjectC Method4 called")
}

func (c *ObjectC) PublicMethod() {
    fmt.Println("ObjectC PublicMethod called")
    c.privateMethod()
}

func (c *ObjectC) privateMethod() {
    fmt.Println("ObjectC privateMethod called")
}

type MasterObject struct {
    objectA *ObjectA
    objectB *ObjectB
    objectC *ObjectC
}

func NewMasterObject() *MasterObject {
    m := &MasterObject{
        objectA: &ObjectA{},
        objectB: &ObjectB{},
        objectC: &ObjectC{},
    }

    m.objectA.onEvent1 = func() {
        m.objectB.Method1()
    }

    m.objectA.onEvent2 = func() {
        result := m.objectB.Method2()
        m.objectA.HandleResponse(result)
    }

    m.objectA.onEvent3 = func() {
        result := m.objectB.Method3()
        if result {
            m.objectA.HandleTrue()
        } else {
            m.objectA.HandleFalse()
        }
    }

    m.objectA.onEvent4 = func() {
        m.objectB.Method4()
        m.objectC.Method4()
    }

    return m
}
```