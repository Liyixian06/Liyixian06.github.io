---
layout:		 single
title:       "Quality Assurance 03 Test Design"
subtitle:    ""
description: " "
date:        2025-11-03T19:14:17-05:00
author: LiYixian
image:       ""
tags:        ["cs", "quality assurance"]
categories:  ["Tech" ]
URL: "2025/11/quality-assurance-03/"
math: False
---

**Overview**:  

1. How to select high-value test inputs
2. The basic concepts of blackbox and whitebox testing
	- Tradeoffs
	- Effort
	- Strengths and weaknesses
3. Several popular methods for generating test inputs

### Blackbox Testing

- Tests are created according to the specification for software
	- documentation, requirements, APIs, ...
- Checks whether software matches that specification
	- i.e., does the code do the right thing?
	- can reveal incomplete, ambiguous, or erroneous specifications
- Code structure does not inform test case design

Why is blackbox testing useful?  
- Sometimes you don’t have source code!
- Tests can be written before the implementation exists!
- Test design is unbiased by implementation
- Tests are written with functionality in mind
- Test design can improve your API design and specification

### Input Generation
#### Random Testing

Test a random sample of inputs.

- Simple approach: Sample candidate inputs uniformly
	- Assumes that all inputs are equally valuable
- Problem: Faults are not uniformly distributed
- Used effectively in specific domains
#### Boundary Value Testing

> There are two hard things in computer science: cache invalidation, naming things, and off-by-one errors. — Jeff Atwood

Test boundaries values for each variable.

- Key Insight: Errors tend to occur at the boundaries of a variable value  
- Relies on the single fault assumption
- For each variable, select five values:
	- Minimum
	- Immediately above minimum
	- Nominal value (e.g., midpoint)
	- Immediately below maximum
	- Maximum
#### Robustness Testing

#### Partition Testing

- Partition of a set, usually the input domain of the program, based on some equivalence relation/class  
	- Partitions should be disjoint, complete, and uniform (e.g., life stages, regional divisions, ...)
- Generate a test input per partition

Equivalence class testing can be applied to factors other than the value of a variable.

- Syntactic (mechanical)/Structural (intelligent) attributes
	- e.g., the length of a string, the number of occurrences of an element, program output, etc.
	- Syntactic: Directly inferred from attributes, their types or natural properties / states / categories and boundary values of the types
		- null, unsigned int range, order of array, input device, ...
	- Semantic: Indirectly inferred from attributes (possibly a property of outputs or category of execution side effect)
- Many software failures are caused by the mistreatment of “special” (but otherwise correct) cases such as: 
	- null entries
	- entries with maximum lengths
	- whether a character string contains spaces or not
	- /r/n vs. /n newlines delimiters
	- whether the treatment of a particular piece of data is the same irrespective of 
		- its order in a sequence
		- whether it occurs more than once

Boundary values and equivalence classes: Errors can occur at the boundaries of equivalence classes  
(Beware: This can lead to a large number of tests!)
#### Combinatorial Testing

Finds failures caused by interactions between variables.

Combinatorial Testing is not All-Combinations Testing: Test for n-way interactions between variables  
Very few additional errors are found as we move beyond testing all 5-way interactions.

Use tools to generate combinatorial tests (ACTS, Comtest, Jcunit, ...)

#### Decision Tables

![](/img/Decision_Tables.png)

- When there are logical relationships between variables
  - the value of one variable constrains the values of other variables
  - e.g., dollars spent on an order affects shipping + voucher eligibility
- When complex inputs can be effectively described by binary properties
- Actions are unequivocal
  - the order in which conditions are evaluated should not affect the interpretation of the rules

### Whitebox Testing

Write; Measure; Repeat  

Adequacy criteria:
- Control flow
	- Statement, Branch, Path, Loop (0/1/1+ times), Condition
- Mutation: Provides an approximate measure of how well a given test suite reveals faults in the program
- Data flow: Based on testing how variables are used and defined



**Summary**:

1. There are many approaches to blackbox & whitebox testing
2. Each approach has associated tradeoffs:  
	- intuition vs. systematic
	- domain knowledge vs. automation
	- number of tests
	- redundancy
	- relationships between variables
	- ...
3. Tools can automatically generate test cases
