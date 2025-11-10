---
layout:		 single
title:       "Quality Assurance 07 Test Oracles"
subtitle:    ""
description: " "
date:        2025-11-10T14:07:14-05:00
author: LiYixian
image:       ""
tags:        ["cs", "quality assurance"]
categories:  ["Tech" ]
URL: "2025/11/quality-assurance-07/"
math: False
---

All tests we have written so far are example-based: pick specific inputs, hard-code expected outputs  
=> But real systems have huge input spaces and even good test suites miss bugs. 

What if we let the computer explore the input space for us?

### Generating Inputs via Fuzzing

Fuzz testing randomly generates inputs and checks for program crashes.  

- Mutation-based fuzzing (e.g., Radamsa)
	- binary input, text input, GUI input, etc.
- Coverage-guided fuzzing (e.g., AFL)

Fuzzers can generate millions of inputs. **How do we check if the program is correct?**

### Oracles

- An oracle decides if behavior is correct for a given input
	- strong oracles catch bugs that weak oracles miss  
	- designing strong oracles is difficult and often the bottleneck

From easy to difficult: `max(a,b)` => route planning service => AI-based article summarization service => autonomous rideshare vehicle

- Assertions in Example-Based Tests
	- most common type
	- these assertions are often hardcoded to a specific test input
- Snapshot Tests
	- records an approved “golden” output for a provided input during system execution
	- useful for complex but stable outputs
	- Can be brittle and encourage bad practices:
		- buggy behavior can be “blessed” by the snapshot
		- snapshots can fail the test for harmless changes (white spacing, padding, etc.)
- The Program Shouldn’t Crash!
	- used by most fuzzing approaches
	- generic property that is not tied to any test inputs, but the oracle is very weak
- Assertions in Source Code
	- executable specifications
		- document intended behavior (pre/postconditions, invariants)
	- generic and not tied to any test inputs (if we add assertions, we can use fuzzing to find some logic bugs!)
	- assertions state invariants: conditions that must always hold if the program is correct (e.g., impossible states, internal consistency); use exceptions and returns for errors that can reasonably happen and should be handled (e.g., invalid inputs, failed API calls).

### Property-Based Testing

1. You state general rules (**properties**) that must always hold  
2. A **generator** is used to randomly sample many inputs
	- `fc.integer(...), fc.string(...), fc.array(...), fc.record(...), ...`
3. The test runner tries to find a counterexample and shrinks it to a minimal failing case

example: testing a sorting algorithm
```java
function isNonDecreasing(values: number[]): boolean {
	for (let i = 1; i < values.length; i++) {
		if (values[i - 1] > values[i]) return false;
	}
	return true;
}
fc.assert(fc.property(fc.array(fc.integer()), xs => {
	const ys = doubleBogosort(xs);
	return nonDecreasing(ys);
}));
```
Real-world cases:
- Compilers and Optimizers
- APIs and Services
- Robotics and Cyberphysical Systems
- Generative AI and Agentic Systems
	- ensure that agents do not perform certain actions under specific conditions (e.g., agent must only look at information related to the customer that started the interaction)

#### Identifying Properties

- Preservation: something stays the same or within allowed bounds
```java
fc.assert(fc.property(fc.array(Item), fc.tuple(Tier,Tier), (items,[tLow,tHigh]) => {
	const order = ["guest","bronze","silver","gold"];
	const low = computeTotal(items, tLow);
	const high = computeTotal(items, tHigh);
	return order.indexOf(tHigh) >= order.indexOf(tLow) ? high <= low : true;
}));
```
- Metamorphic: property holds under input transformations
```java
fc.assert(fc.property(fc.array(fc.integer()), xs => {
	const a = doubleBogosort(xs);
	const b = doubleBogosort(xs.reverse());
	return a.length === b.length && a.every((v,i)=> v === b[i]);
}));
```
- Differential: two implementations (or versions) agree on outputs and errors
```java
fc.assert(fc.property(fc.array(fc.integer()), xs => {
	const a = doubleBogosort(xs);
	const b = radixSort(xs);
	return a.length === b.length && a.every((v,i)=> v === b[i]);
}));
```
#### Generating Inputs via Arbitraries

Arbitraries are used to describe input spaces  

```java
const Price = fc.double({ min: 0, noNaN: true }); 
const Qty = fc.integer({ min: 1, max: 10 }); 
const Item = fc.record({
	sku: fc.string({ minLength: 1, maxLength: 12 }),
	unitPrice: Price,
	qty: Qty,
});
const Cart = fc.record({
	items: fc.array(Item, { maxLength: 15 }), 
});
```
