import subprocess
import re
import matplotlib.pyplot as plt
import argparse
import os

outfile_git_name = "tmp_git.txt"
outfile_format_name = "tmp_formatted.txt"

git_log_constant = "1 file changed, "  # Used for grep, do not modify

diff_list = []
total_list = []

# Parse arguments passed by command line
parser = argparse.ArgumentParser()
parser.add_argument("filepath", help="Relative or absolute path to the file you want to measure")
parser.add_argument("-p", help="Use points instead of line in graphs", action='store_true')
parser.add_argument("--y_line", help="Draw horizontal line on y position (integer)", type=int)
parser.add_argument("--gitdir",
         help="Specify repository directory if the file to measure is in a ouside repository. "
            + "(Relative or absolute)")

args = parser.parse_args()

filepath = args.filepath
custom_y = args.y_line
use_point = args.p

if not os.path.isfile(filepath):
    raise ValueError("NOT A FILE: " + filepath)


#git "--git-dir=/home/repo/"
command_git_log = "git"

if args.gitdir != None:
    command_git_log += " -C " + args.gitdir

command_git_log += " log --stat --pretty=format: " + filepath

    
def is_insertion(str):
    return str == "insertion" or str == "insertions"


def get_stats(line):
    words = re.findall("\w+", line)

    current_diff = 0

    # Magic number 4 to avoid "1 file changed" string
    for i in range(4, len(words), 2):
        if is_insertion(words[i]):
            current_diff += int(words[i-1])
        else:
            current_diff -= int(words[i-1])

    diff_list.append(current_diff)


with open(outfile_git_name, "w") as outfile:
    subprocess.call(command_git_log.split(), stdout = outfile)

with open(outfile_format_name, "w") as outfile:
    subprocess.call(["grep", git_log_constant, outfile_git_name], stdout = outfile)


# Delete tmp file
subprocess.call(["rm", outfile_git_name])

with open(outfile_format_name) as f:
    for line in f:
        get_stats(line)


# Delete tmp file
subprocess.call(["rm", outfile_format_name])


# I dont want to throw an Error.. 
if (len(diff_list) == 0):
    msg_no_lines = "\nThe file " + filepath + " never had any lines ever! \n" 
    msg_no_lines += "Probably it is located in an external repository and you didn't specyfy --gitdir"
    
    print(msg_no_lines)


else:
    # Reverse diffs to be in incremental time
    diff_list.reverse()
    total_list.append(diff_list[0]) # Need at least one element

    total_max = total_list[0]

    for i in range(1, len(diff_list)):
        total_list.append(total_list[i-1] + diff_list[i])
        if (total_list[-1] > total_max):
            total_max = total_list[-1]

    total_current = total_list[-1]

    # plot
    if (use_point):
        plt.plot([i for i in range(1, len(total_list) + 1)], total_list, 'bo')
    else:
        plt.plot(total_list)
    plt.grid()
    plt.title(filepath)
    plt.ylabel('File lines')
    plt.xlabel('Commits')

    # Plot max line
    plt.axhline(y=total_max, color='r', linestyle='-')
    plt.text(len(total_list)/2, total_max + 1, r'max=' + str(total_max))    

    # Plot custom line
    if (custom_y != None):
        plt.axhline(y=custom_y, color='g', linestyle='-')
        plt.text(len(total_list)/2, custom_y + 1, r'custom=' + str(custom_y))        

    # Plot current line
    if (total_current != total_max):
        plt.axhline(y=total_current, color='b', linestyle='-')
        plt.text(0, total_current + 1, r'curr=' + str(total_current))

    plt.show()
