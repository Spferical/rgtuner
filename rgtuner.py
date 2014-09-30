#!/usr/bin/env python2
from __future__ import print_function
import argparse
import subprocess
import re
import os
import shutil
import copy
import multiprocessing


def make_variants(variable, robot_file, possibilities):
    """Makes variants of the file robot_file  with the constant variable
    changed for each possibility.

    e.g. if the variable is "ELEPHANTS" and the possibilities are [1, 2, 3],
    this will find the line
    ELEPHANTS = 3
    in robobt_file and make a copy of the file for each value in possibilities.
    1.py will have ELEPHANTS = 1, 2.py will have ELEPHANTS = 2, etc.

    Raises IndexError if the variable name is not found in the file robot_file.
    The line assigning the constant variable must be the first line in that
    file has the variable name in it.
    """
    filenames = []
    with open(robot_file, 'r') as f:

        lines = f.readlines()

        i = 0
        while not variable in lines[i]:
            i += 1

        assert '=' in lines[i]

        for p in possibilities:

            lines[i] = variable + " = " + str(p) + '\n'
            filenames.append(variable + str(p))

            with open(variable + str(p), 'w') as pfile:
                for line in lines:
                    pfile.write(line)

    return filenames


def get_current_value(variable, robot_file):
    """
    Returns the value of the constant variable in the robot file.

    This function finds the first line in the file robot_file that has the
    variable name in it, and parses the value after the '=' in that line for a
    float, returning it.

    Raises IndexError if the variable name is not found in the file robot_file.
    The line assigning the constant variable must be the first line in that
    file has the variable name in it.
    """
    with open(robot_file, 'r') as f:
        lines = f.readlines()

        i = 0
        while not variable in lines[i]:
            i += 1

        assert '=' in lines[i]

        value = float(lines[i][lines[i].index('=') + 1:])

    return value


def optimize_variable(enemy, variable, robot_file, processes):
    """
    Creates a bunch of variants of the file robot_file, each with variable
    changed, then runs a tournament between the variants to find the best one.
    The file robot_fily is modified to contain the best value, and it is
    returned.
    """
    base_value = get_current_value(variable, robot_file)

    precision = 8.0

    while precision >= 0.1:

        print('RUNNING WITH BASE VALUE', base_value, \
                'PRECISION', precision)

        values_to_test = [
            base_value - precision,
            base_value + precision,
            base_value
        ]

        files = make_variants(variable, robot_file, values_to_test)
        best_file = run_tourney(enemy, files, processes)
        best_value = values_to_test[files.index(best_file)]
        if best_value == base_value:
            precision = precision / 2.0
            print('best value remains', best_value)
            print('decreasing precision to', precision)
        else:
            base_value = best_value
            print('new \'best\' value is', best_value)

    shutil.copy(make_variants(variable, robot_file, [base_value])[0],
                robot_file)

    return base_value

def run_match(bot1, bot2):
    """Runs a match between two robot files."""
    p = subprocess.Popen(
        'rgrun -H ' + bot1 + ' ' + bot2,
        shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    pall = re.compile('\d+')

    try:
        for line in p.stdout.readlines():
            if line[0] == '[':
                scores = pall.findall(line)
                if scores[0] > scores[1]:
                    return [int(scores[0]),int(scores[1]), int(scores[0]) - int(scores[1]),bot1]
                elif scores[1] > scores[0]:
                    return [int(scores[0]),int(scores[1]), int(scores[0]) - int(scores[1]),bot2]
                else:
                    return [int(scores[0]),int(scores[1]), int(scores[0]) - int(scores[1]),'tie']


                
    except KeyboardInterrupt:
        p.terminate()


def versus(bot1, bot2, processes):
    """Launches a multithreaded comparison between two robot files.
    run_match() is run in separate processes, one for each CPU core, until 100
    matches are run.
    Returns the winner, or 'tie' if there was no winner."""
    bot1Score = 0
    bot2Score = 0

    matches_to_run = 100

    pool = multiprocessing.Pool(processes)

    print('launching comparison in', processes, 'processes')

    try:
        results = [pool.apply_async(run_match, (bot1, bot2))
                   for i in range(matches_to_run)]

        for r in results:
            score = r.get(timeout=120)
            print('battle result:',score[3], ' difference:', score[2])
            bot1Score += score[0]
            bot2Score += score[1]
            
            #otherwise, it's a tie, but we can ignore it

        pool.close()
        pool.join()

        print('overall:', bot1, bot1Score, ':', bot2Score, bot2)
        return bot1Score - bot2Score

    except KeyboardInterrupt:
        print('user did ctrl+c, ABORT EVERYTHING')
        pool.terminate()
        raise KeyboardInterrupt()

def run_tourney(enemy, botfiles, processes):
    """Runs a tournament between all bot files in botfiles.
    Returns the winner of the tournament."""
    bestWin = ['', -5000]
    botfiles = copy.copy(botfiles)

    while len(botfiles) > 0:
        bot1 = botfiles[0]
        winScore = versus(bot1, enemy, processes)
        while winScore == 0:
            print('VERSUS WAS A TIE. RETRYING...')
            winScore = versus(bot1, enemy, processes)
        botfiles.remove(bot1)
        if winScore > bestWin[1]:
            bestWin[1] = winScore
            bestWin[0] = bot1
        else:
            os.remove(bot1)
        print('Difference in score:',str(bestWin[1]))

    
    print('Best Score:',str(bestWin[1]))
    return bestWin[0]


def main():
    parser = argparse.ArgumentParser(
        description="Optimize constant values for robotgame.")
    parser.add_argument(
        "constant", type=str, help='The constant name to optimize.')
    parser.add_argument(
        "file", type=str, help='The file of the robot to optimize.')
    parser.add_argument(
        "enemy", type=str, help='The enemy file.')
    parser.add_argument(
        "-p", "--processes",
        default=multiprocessing.cpu_count(),
        type=int, help='The number of processes to simulate in')
    args = vars(parser.parse_args())

    best_value = optimize_variable(args['enemy'],
        args['constant'], args['file'], processes=args['processes'])
    print(best_value)


if __name__ == '__main__':
    main()
