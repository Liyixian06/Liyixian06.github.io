---
layout:		 single
title:       "Quality Assurance 05 Test Doubles"
subtitle:    ""
description: " "
date:        2025-11-03T11:31:09-05:00
author: LiYixian
image:       ""
tags:        ["cs", "quality assurance"]
categories:  ["Tech" ]
URL: "2025/11/quality-assurance-05/"
math: False
---

### End-to-End Testing

A single test can provide lots of coverage, but:  

- Can be fragile
- Have poor isolation
	- redundancy (e.g., initialization, route forwarding, ...)
- Difficult to automate
	- test environment
- Slow and expensive

-> Unit Testing!

### Test Doubles

We substitute external collaborators with test doubles.

#### Dummy

Objects that are needed by the program (e.g., parameters) but are never actually used.

```javascript
public interface Logger {
    public void append(String message);
}

public class LoggerDummy implements Logger {
    public void append(String message) {
        // we do nothing!
	}
}
```
#### Stub

Double for a real collaborator that gives predefined answers to calls during testing.

Use it if you just want collaborators to provide canned responses.

``` javascript
// Pass in a stub that was created by a mocking framework.
AccessManager accessManager = new AccessManager(stubAuthenticationService);

// The user shouldn't have access when the authentication service returns false.
when(stubAuthenticationService.isAuthenticated(USER_ID).thenReturn(false);
assertFalse(accessManager.userHasAccess(USER_ID));)

// The user should have access when the authentication service returns true.
when(stubAuthenticationService.isAuthenticated(USER_ID)).thenReturn(true);
assertTrue(accessManager.userHasAccess(USER_ID));
```

#### Fake

Provides an optimized, thinned-down version of a collaborator that replicates the same behavior of the original object without certain side effects or consequences.

Use it if you test a complex scenario that relies on a service or
component that’s unavailable or unusable for your test’s purposes, and stubbing does not do the job (e.g., database driver).

``` javascript
/*
Behaves like a real ProductDatabase that accesses a database, but is simpler, faster, and side-effect free.
*/
public class FakeProductDatabase implements ProductDatabase {
  private Collection<Product> products = new ArrayList<Product>();
  public void save(Product product) {
    if (findById(product) == null)
      products.add(product);
  }
  public Product findById(long id) {
    for (Product product : products) {
      if (product.getId() == id) return product;
    }
    return null;
  }
}
```
#### Spy

Observes calls and arguments to a collaborator without changing behavior.

```javascript
class Checkout {
      constructor(private pay:{ charge(n:number):Promise<void> }){}
      submit(total:number){ return this.pay.charge(total); }
}

const stripeAdapter = { charge: async (_:number)=>{} };
const spy = vi.spyOn(stripeAdapter,
'charge').mockResolvedValue(undefined);

await new Checkout(stripeAdapter).submit(1299);

expect(spy).toHaveBeenCalledWith(1299);
```

#### Mock

Used to test for expected interactions with a collaborator (i.e., method calls).
Allows calls to be observed (spy-like) and behavior to be changed (stub-like).

Use it if you want to test interactions between SUT and DOC.

```javascript
// Pass in a mock that was created by a mocking framework.

AccessManager accessManager =new AccessManager(mockAuthenticationService); accessManager.userHasAccess(USER_ID);

// The test should fail if accessManager.userHasAccess(USER_ID) didn't call
// authenticationService.isAuthenticated(USER_ID) or if it called it more than once.
verify(mockAuthenticationService).isAuthenticated(USER_ID);
```

### Best Practices

- Don’t share doubles between tests, except possibly fakes
- Only stub the behavior that is interesting for the current test
- Assert the minimum!
	- Prefer the weakest double
		- (−intrusive) Stub < Fake < Spy < Mock (+intrusive)
	- For queries (i.e., returning data), use a Stub or Fake
	- For commands (i.e., cause effects), use a Spy, Mock, or Fake
