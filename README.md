# dependent-type
For CS2520R Assignment 1

Have two parts to this assignment

The first part is 'dependent.py' which is the implementation of the semantic model (or at the very least a close implementation of the semantic model) for implementing Dependent Types with capture-avoiding substitution and has examples testing commutative property for addition and associative property for multiplication [3]. Also attempted to address alpha-equivalence using De Bruijn indices (dependent_index.py) to replace variable names with natural numbers that represent the number of binders between the variable's occurrence and its binding site, however, it doesn't really work and the example at the end of the script fails.

Can run this code by cloning the repository, cd into the repository folder, and running 'python dependent.py' locally.

As an alternative to the dependently typed assignment, there is included a separate semantic model for implementing polymetric polymorphism using STLC and the corresponding type set as a PDF [1,2].

References:

[1] [https://www3.nd.edu/dchiang/teaching/pl/2022/f.html](https://www3.nd.edu/~dchiang/teaching/pl/2022/f.html)

[2] [https://www.cs.utexas.edu/bornholt/courses/cs345h-24sp/lectures/8-system-f/](https://www.cs.utexas.edu/~bornholt/courses/cs345h-24sp/lectures/8-system-f/)

[3] https://github.com/sabrinahu5/program-synthesis/blob/main/interpreter/flashfill-interpreter/ff-interpreter.py#L148
