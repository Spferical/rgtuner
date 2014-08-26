rgtuner
=======

rgtuner is a program to 'tune' bots for robotgame.org by modifying one variable
at a time, throwing versions of a bot with different possible values for the
variable against each other and seeing which comes out on top.

#Requirements
- Python
- rgkit

#Usage
`$ python rgtuner.py [-h] [-p PROCESSES] constant`
e.g. `$ python rgtuner.py -p 6 SURROUND_WEIGHT` to optimize the
SURROUND_WEIGHT variable, running comparisons in 6 different processes.
