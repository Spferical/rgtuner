rgtuner
=======

rgtuner is a program to 'tune' bots for robotgame.org by modifying one variable
at a time, throwing versions of a bot with different possible values for the
variable against each other and seeing which comes out on top.

Included is an example bot, a version of Sfpar. All of the globals are added at
the beginning of the file. This program is what I used to create Sfpar II: I
merely optimized the variables in it.

rgtuner can't necessarily be used to find the optimum behavior for your bot as
it uses a greedy algorithm, but the 'tuned' version of the bot should perform
slightly better against the old one.

#Requirements
- Python
- rgkit

#Usage
`$ python rgtuner.py [-h] [-p PROCESSES] constant`
e.g. `$ python rgtuner.py -p 6 SURROUND_WEIGHT` to optimize the
SURROUND_WEIGHT variable, running comparisons in 6 different processes.
