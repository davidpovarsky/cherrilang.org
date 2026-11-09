---
title: Functions
layout: default
parent: Documentation
nav_order: 12
---

# Functions
{: .no_toc }

Functions are an abstraction on top of your Shortcut that allows you to run actions separately from your main actions, multiple times, and optionally recurse and/or output a value.

This allows you to reduce duplicate action code and overall cut down on the total actions in your Shortcut if you have actions doing the same thing in multiple places.

This abstraction is injected at the top of your Shortcut. [The first comment is preserved](#prioritization-of-instructional-or-contact-comments).

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

## Definition

### Defining a Function

Define your action, then reference the action to run the contents of the function, isolated from the rest of your Shortcut:

```cherri
function add(op1: Number, op2: Number) -> Number {
    let result = op1 + op2
    return result
}

let sum = add(2, 2)
```

Keep in mind that if a function is used, the compiler will inject some actions at the top of your Shortcut to support this feature.

### Defining Arguments

You can define arguments for your function that you provide later when referencing it.

```cherri
function myAction(message: Text) {
    show(message)
}
```

Read the [types](types) reference for all types you can use for arguments.

When calling your function, keep in mind that the arguments you use will be type-checked against your type definitions for each of your arguments.

Each argument is currently defined and treated as a variable.

### Optional

Add a `?` after the argument name to mark it as optional, meaning it is not required to be filled in. Otherwise, the compiler will complain if the argument is not filled in when the function is called.

```cherri
function myAction(message?: Text) {
    show("Executed")
}
```

### Literal Parameters

In Cherri v2, user-defined function parameters accept runtime expressions and variables. Literal constraints apply only to built-in action parameters that require compile-time constants.

### Default Value

You can optionally use an assignment operator to set a default value for the argument. The compiler will warn against using the default value for this argument, as that will make for a smaller shortcut.

```cherri
function myAction(message: Text = "Hello, World!") {
    show(message)
}
```

## Function Behavior

### Returning a Value

This is not required, but if you would like to return a value from your function to a call and assign the reference to a variable, just like you would with a standard action.

Then, inside the body of your function, use the `return` statement to return a result.

```cherri
function myFunc() -> Text {
    return "Hello!"
}

let result = myFunc()
```

### Output Type

You can define an output type for your function so that an error can be thrown if the output is used where that type is not expected.

```cherri
function sum(op1: Number, op2: Number) -> Number {
    return op1 + op2
}
```

### Output Type Coercion

Type coercion is be done at the action call level, where the output of the action will be put in a type casting action, such as a text or number action, and then assigned to the variable for the return variable, but only if there is one.

### Isolated Scope

Functions run in a completely separate Shortcut instance via `runSelf()`. Variables from the outer Shortcut are not accessible inside a function body — the new instance starts with no state.

{: .important }
All data a function needs must be passed as arguments. Referencing an outer variable inside a function body will produce a compiler error.

```cherri
let greeting = "Hello"

function greet(name: Text) {
    // greeting is NOT accessible here
    show(f"Hi, {name}!")
}

greet("World")
```

### Recursion

It is possible to call other functions within the body of a function. You can then use this for recursion, running the same function with an eventual breakpoint.

{: .warning }
Misuse of recursion can cause a Shortcut to infinitely loop.

```cherri
function fibonacci(n: Number) -> Number {
    if n <= 1 {
        return n
    } else {
        let minusOne = n - 1
        let minusTwo = n - 2
        let fib1 = fibonacci(minusOne)
        let fib2 = fibonacci(minusTwo)
        let added = fib1 + fib2
        return added
    }
}

let output = fibonacci(7)
show(f"{output}") // 13
```

## Prioritization of Instructional or Contact Comments

Note that when the compiler reaches your first explicit comment action, if you are using a function, it will push that action to the top of the Shortcut instead of adding it after the injected functions abstraction has been added at the top.

This is primarily to still be able to add an instructional or contact comment at the top of a Shortcut while also using the functions abstraction.

```cherri
comment("Contact me: brandon@cherrilang.org")

function greet(name: Text) -> Text {
    return f"Hello, {name}!"
}

let message = greet("World")
show(message)
```

## How Do They Work?

The contents of functions run separately from your main code inside your Shortcut by using the **Run Shortcut** action and passing a **Dictionary** action containing data that will be detected by the injected Cherri code that contains each of the defined actions that are used in the Cherri code below it.

This is a part of the language that does not translate 1-1, but for the functionality it provides, it can be a powerful tool.

### Action Definition

The semantics of this may change over time, but it roughly translates to this in Cherri:

```cherri
if ShortcutInput {
    let inputType = typeOf(ShortcutInput)
    if inputType == "Dictionary" {
        let input = getDictionary(ShortcutInput)
        let identifier = getValue(input, "cherri_functions")
        let valid = number(identifier)
        if valid == true {
            let function_name = getValue(input, "function")
            let fn = f"{function_name}"
            let args = getValue(input, "arguments")
            if fn == "add" {
                let arg1 = getListItem(args, 0)
                let arg2 = getListItem(args, 1)
                let op1 = number(arg1)
                let op2 = number(arg2)
                let result = op1 + op2
                show(f"{result}")
            }
        }
    }
}
```

The compiler will generate this syntax and inject it into the top of the resulting Shortcut.

It validates that the input we're receiving is a Cherri function call, then filters it down to which action is being called, then we have actions based on the action's definition that coerce the provided argument values from the input into their defined value types, then the injected function body is run.

At the end, just in case no output was defined in the function body that was called, we output nothing at the end of the action call list.

### Function Calls

Then, when you reference the function described `add(number, number)`

```cherri
function add(op1: Number, op2: Number) -> Number {
    let result = op1 + op2
    return result
}

let sum = add(2, 2)
```

It will create tokens in the compiler for a **Dictionary** and a **Run Shortcut** action equivalent to this:

```cherri
let addCherriCall = {
    "cherri_functions": 1,
    "function": "add",
    "arguments": [2, 2]
}

runSelf(addCherriCall)
```
