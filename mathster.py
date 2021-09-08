#!/usr/bin/env python3

import json
import os
import random
import re
import sys
import time

#This should be backwards and forwards compatible with python2 or 3
try:
    buildins_dict = __builtins__.__dict__
except AttributeError:
    buildins_dict = __builtins__
if not 'raw_input' in buildins_dict.keys():
    #Python3
    text_input = input #pylint: disable=invalid-name
    from pathlib import Path
else:
    #Python2
    text_input = buildins_dict['raw_input'] #This is done this way because IDE's complain
    try:
        from pathlib2 import Path #pylint: disable=unused-import
    except ImportError:
        class Path(object): #pylint: disable=too-few-public-methods
            """
            Create a Path object that can simulate python3's Path.home()
            """
            @staticmethod
            def home(self=None): #pylint: disable=bad-staticmethod-argument,unused-argument
                """
                Return the expanded path to the user's home
                """
                return os.path.expanduser('~')

# These are defaults
MAX_MIN = 10
LEFT_HAND = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
RIGHT_HAND = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
ALLOW_SUB_NEGATIVE_ANS = 'no'
ALLOW_SUB_MULTI_DBL_QUESTION = 'no'
REWARD_TIME_SEC = 20
KNOWN_OPERATORS = ( '+', '-', '*', 'x', '/' )
ENCOURAGEMENTS = (
    "I'm sorry, that's not quite right you silly goose!\n\nAnswer: {answer}",
    "Come on! I know you've got this!\n\nAnswer: {answer}",
    "Remember, you fail ALL of the times you don't try! I'm proud of you for trying!\n\nAnswer: {answer}",
    "The harder something is, the better you'll feel when you've mathstered it! Try again!\n\nAnswer: {answer}",
)
CONGRATULATIONS = (
    "Correct! Your answer was worth: {points} points!",
    "Woohoo! All this practice appears to be paying off! You just earned {points} more points!",
    "Oh Yeah! SOMEONE just showed they know an answer!: {points} more points!",
    "Boy! I just can't fool you now can I!!? have {points} more points!,"
)
# Paths and where to find things
USER_HOME = str(Path.home())
STATE_FILE_DIR = '{}/mathster'.format(USER_HOME)
SCORING_MATRIX = {
    '*': (
        (10, 1), # less than == 10 is 1 point
        (30, 2),
        (45, 3),
        (55, 4),
        (70, 5),
        (99, 6),
        (100, 10), # Anything bigger than this is also worth 10
    ),
    '-': (
        (1, 4), # Subtraction are worth 4 points (Make it similar point value as '*')
        (100, 4),
    ),
    'default': 2,
    'bonus': 15
}

POINTS_TO_REWARD_VAL = 0.0125 #Every this many points == 1min reward time

##- Functions -##
def clear():
    if os.name == 'posix':
        os.system('clear')
    else:
        os.system('cls')

def get_ans(lh, rh, op):
    ans = None
    if op == '+':
        ans =  lh + rh
    elif op == '-':
        ans =  lh - rh
    elif op in [ 'x', '*' ]:
        ans =  lh * rh
        op = '*'
    elif op in [ '/' ]:
        ans =  lh / rh
        op = '/'
    else:
        print("Unknown operator: '{}'".format(op))
        sys.exit(1)
    return (ans, op)

def get_score_value(ans, op):
    matrix = SCORING_MATRIX.get(op, None)
    if matrix == None:
        return SCORING_MATRIX['default']
    for pval, score in matrix:
        if ans <= pval:
            return score
    return score

def gen_tuples(left_hand, right_hand, operators, allow_sub_neg_ans=False, allow_sub_mult_dbl_q=False, **kwargs):
    tuples = []
    for lh in left_hand:
        for rh in right_hand:
            for op in operators:
                if op == '-':
                    # We only want subtraction to have postive answers for now
                    if not allow_sub_neg_ans:
                        if lh < rh:
                            continue
                    # We only want subtraction to be one double digit minus a single digit
                    if not allow_sub_mult_dbl_q:
                        if lh >= 10 and rh >= 10:
                            continue
                tuples.append((lh, rh, op))
    return tuples

def get_valid_int(minimum=0, maximum=-1, default=None, prompt="Enter Integer (default={default})", error_prompt='Incorrect integer inputed: \'{int_input}\'. Must be an Integer between {minimum} and {maximum}'):
    prompt = '{}: '.format(prompt)
    while True:
        try:
            int_input = text_input(prompt.format(default=default))
        except:
            sys.exit(1)
        if int_input == '':
            if default != None:
                int_input = default
        if int_input == 'exit':
            return None
        try:
            int_input = int(int_input)
            if maximum < 0:
                if int_input < minimum:
                    raise ValueError
            else:
                if int_input < minimum or int_input > maximum:
                    raise ValueError
        except ValueError:
            max_str = maximum
            if maximum < 0:
                max_str = 'inf'
            print(error_prompt.format(int_input=int_input, minimum=minimum, maximum=max_str))
            continue
        break
    return int_input

def get_user_input(prompt='Enter a value (default={default})', allow_empty=False, default=None, yesno=False):
    prompt = '{}: '.format(prompt)
    while True:
        try:
            resp = text_input(prompt.format(default=default))
        except:
            sys.exit(1)
        if not resp:
            if default:
                resp = default
        if yesno:
            if resp.lower() in ('yes','y'):
                return True
            elif resp.lower() in ('no', 'n'):
                return False
            else:
                print("Invalid response, must be one of 'yes, y, no, n'")
                continue
        if allow_empty:
            return resp
        else:
            if not resp:
                print("You must provide an answer")
                continue
            else:
                return resp

def get_selection_menu(options, enabled_options=None, title=None, loop_title=None, show_all=False, show_done=False):
    enabled_opts = []
    if enabled_options:
        enabled_opts = list(enabled_opts)
    if title:
        print(title)
    if show_done:
        print("NOTE: enabled = *")
    while True:
        for idx, opt in enumerate(options, start=1):
            pre_str = ''
            if show_done:
                pre_str = '[ ]'
                if opt in enabled_opts:
                    pre_str = '[*]'
            print("  {idx} - {pre_str}{opt}".format(idx=idx, pre_str=pre_str, opt=opt))
        options_len = len(options)
        extra_opts = 0
        if show_all:
            extra_opts += 1
            all_opt = options_len + extra_opts
            print("  {opt} - ALL".format(opt=all_opt))
        if show_done:
            extra_opts += 1
            done_opt = options_len + extra_opts
            print("  {opt} - Done".format(opt=done_opt))
        try:
            selection = text_input("Selection: ").strip()
        except:
            sys.exit(1)
        try:
            sel_idx = int(selection)
        except ValueError:
            print("Incorrect option: '{}' . Must be an Integer".format(selection))
            continue
        if show_done:
            if sel_idx == done_opt:
                break
        if show_all:
            if sel_idx == all_opt:
                for idx, opt in enumerate(options, start=0):
                    if opt in enabled_opts:
                        enabled_opts.remove(opt)
                        continue
                    enabled_opts.append(opt)
                if not show_done:
                    break
                if loop_title:
                    print(loop_title)
                continue
        if sel_idx < 1 or sel_idx > options_len + extra_opts:
            print("\nIncorrect option: {selection}. Must be a number from 1 to {max_idx}".format(selection=selection, max_idx=options_len + extra_opts))
            continue
        option_val = options[sel_idx-1]
        if option_val not in enabled_opts:
            enabled_opts.append(option_val)
        else:
            if show_done:
                enabled_opts.remove(option_val)
        if not show_done:
            break
    return enabled_opts

def print_results(results):
    print("Ending results:\n")
    def human_keys(astr):
        """
        Sorts keys based on human order.. IE 1 is less than 10 etc..

        alist.sort(key=human_keys) sorts in human order
        """
        keys=[]
        for elt in re.split(r'(\d+)', astr):
            elt=elt.swapcase()
            try: elt=int(elt)
            except ValueError: pass
            keys.append(elt)
        return keys
    if results['mastered']:
        print("You MASTERED the following problems! Congratulations!!")
        prob_text = list()
        for mastered in results['mastered']:
            prob_text.append("  {0} {2} {1}".format(*mastered))
        print('  \n'.join(sorted(prob_text, key=human_keys)))
    if results['needs_work']:
        print("\nHere are some problems you should work some more on:")
        needs_work_text = list()
        for needs_work in results['needs_work']:
            needs_work_text.append("  {0} {2} {1}".format(*needs_work))
        print('  \n'.join(sorted(needs_work_text, key=human_keys)))
    else:
        print("You didn't seem to encounter any problems you couldn't solve! Way to go!")

def load_state(new=False):
    state = {}
    if new:
        print("Creating new state profile...")
        state['results'] = {
            'needs_work': [],
            'mastered': [],
        }
        state['level'] = 1
        state['score'] = 0
        
    if os.path.isfile(STATE_FILE):
        with open(STATE_FILE, 'r') as sfile:
            state = json.load(sfile)
    elif not new:
        print("Cannot find save state file: {}".format(STATE_FILE))
    if not 'left_hand' in state:
        left_hand = get_user_input(prompt="Enter the left hand set of number you'd like to use for generating problems. Numbers should be comma separated (default={default})", default=','.join([str(i) for i in LEFT_HAND]))
        state['left_hand'] = [int(i) for i in left_hand.split(',')]
    if not 'right_hand' in state:
        right_hand = get_user_input(prompt="Enter the right hand set of number you'd like to use for generating problems. Numbers should be comma separated (default={default})", default=','.join([str(i) for i in RIGHT_HAND]))
        state['right_hand'] = [int(i) for i in right_hand.split(',')]
    if not 'operators' in state:
        operators = None
        if 'results' in state:
            if state['results']['mastered']:
                operators = state['results']['mastered'][0][2]
            elif state['results']['needs_work']:
                operators = state['results']['needs_work'][0][2]
        elif state['tuples']:
            operators = state['tuples'][0][2]
        if not operators:
            operators = get_selection_menu(options=KNOWN_OPERATORS, title="Enter the operators to use for problems", show_done=True)
        state['operators'] = operators
    #Make sure that we are using known operators
    if not set(KNOWN_OPERATORS).intersection(set(state['operators'])) == set(state['operators']):
        unknown_ops= set(state['operators']).difference(set(KNOWN_OPERATORS))
        print("ERROR! Unknown operator(s): {}".format(', '.join(unknown_ops)))
        sys.exit(1)
    if '-' in state['operators']:
        if not 'allow_sub_neg_ans' in state:
            allow_sub_neg_ans = get_user_input(prompt="Would you like to allow negative answers for subtraction? (default={default})", default=ALLOW_SUB_NEGATIVE_ANS, yesno=True)
            state['allow_sub_neg_ans'] = allow_sub_neg_ans
        if not 'allow_sub_mult_dbl_q' in state:
            allow_sub_mult_dbl_q = get_user_input(prompt="Would you like to allow two double digits to be subracted? (default={default})", default=ALLOW_SUB_MULTI_DBL_QUESTION, yesno=True)
            state['allow_sub_mult_dbl_q'] = allow_sub_mult_dbl_q
    if 'rewards_enabled' not in state:
        state['rewards_enabled'] = get_user_input(prompt="Would you like to enable 'reward minutes' for this profile? (y/n)", yesno=True)
    return state

def redeem_reward_mins(reward_mins, minimum_to_prompt=10):
    reward_mins = int(reward_mins)
    if reward_mins >= minimum_to_prompt:
        while True:
            if get_user_input(prompt="Are you here to redeem your rewards mins? (y/n)", yesno=True, default='no'):
                redeem_amount = get_valid_int(
                    prompt="How many reward minutes would you like to redeem, current balance: {}".format(reward_mins),
                    error_prompt="I'm sorry, you don't have that many minutes. Must enter a number between {minimum} and {maximum}",
                    maximum=int(reward_mins)
                )
                if get_user_input(prompt="You're about to redeem: {} minutes, is that correct? (y/n)".format(redeem_amount), yesno=True):
                    reward_mins -= redeem_amount
                    print("Rewards balance is now: {}".format(reward_mins))
                else:
                    continue
            break
    return reward_mins

def save_state(state):
    with open(STATE_FILE, 'w') as sfile:
        sfile.write(json.dumps(state, indent=4))

def main(load_save=False):
    running = True
    reward_time_base = REWARD_TIME_SEC
    clear()
    if load_save:
        print("Loading save data")
        save_data = load_state()
        try:
            tuples = save_data['tuples']
        except KeyError:
            tuples = gen_tuples(**save_data)
    else:
        save_data = load_state(new=True)
        tuples = gen_tuples(**save_data)
        total_problems = len(tuples)
    results = save_data['results']
    score = save_data['score']
    rewards_enabled = save_data.get('rewards_enabled', False)
    reward_mins = save_data.get('reward_mins', 0)
    level = save_data.get('level', 1)
    operators = save_data['operators']
    left_hand = save_data['left_hand']
    right_hand = save_data['right_hand']
    allow_sub_neg_ans = save_data.get('allow_sub_neg_ans', ALLOW_SUB_NEGATIVE_ANS)
    allow_sub_mult_dbl_q = save_data.get('allow_sub_mult_dbl_q', ALLOW_SUB_MULTI_DBL_QUESTION)
    problem_header_text1 = "### Level: {level} Complete: %{complete} ###\nCurrent Score: {score}"
    problem_header_text2 = "\nLibrary of problems: {num_probs} mastered: {mastered}\nTime Left: {time_left} {time_units}\n"
    if rewards_enabled:
        problem_header_text1 += " ({reward_mins:.3f} reward mins)"
        #Check if we are redeeming reward mins
        new_reward_mins = redeem_reward_mins(reward_mins, minimum_to_prompt=15)
        if int(new_reward_mins) < int(reward_mins):
            print("Saving state file to: {}...".format(STATE_FILE))
            save_state({
                'results': results,
                'tuples': tuples,
                'score': score,
                'reward_mins': new_reward_mins,
                'rewards_enabled': rewards_enabled,
                'level': level,
                'operators': operators,
                'left_hand': left_hand,
                'right_hand': right_hand,
                'allow_sub_neg_ans': allow_sub_neg_ans,
                'allow_sub_mult_dbl_q': allow_sub_mult_dbl_q
            })
            return
    problem_header_text = problem_header_text1 + problem_header_text2
    if level >= 10:
        reward_time = REWARD_TIME_SEC * 2
    end_time = START_TIME + (MAX_MIN * 60)
    while running:
        time_left = end_time - time.time()
        if time_left < 60:
            units = "seconds"
        else:
            time_left = int(time_left/60)
            units = "minutes"
        total_problems = len(tuples) + len(results['mastered']) + len(results['needs_work'])
        print(problem_header_text.format(
            level=level,
            complete=100 - int((len(tuples)/total_problems)*100),
            score=score,
            reward_mins=reward_mins,
            num_probs=len(tuples),
            mastered=len(results['mastered']),
            time_left=int(time_left),
            time_units=units
        ))
        if len(results['needs_work']) > 0:
            if len(results['needs_work']) > 4:
                #If there are more than 4 problems that need work, then favor the ones that need more work
                if random.choice([True, True, False]) or not tuples:
                    work_on = random.choice(results['needs_work'])
                else:
                    work_on = random.choice(tuples)
            else:
                #If there are 1-4 problems that need work then slightly favor one from the main pool of tuples
                if random.choice([True, False, False]) or not tuples:
                    work_on = random.choice(results['needs_work'])
                else:
                    work_on = random.choice(tuples)
        else:
            #Pull from the general list of tuples (unless all of have mastered)
            if not tuples:
                level += 1
                print("CONGRATURATLIONS!!! You've progressed to level {}".format(level))
                tuples = gen_tuples(left_hand, right_hand, operators)
                results['mastered'] = []
                results['needs_work'] = []
            work_on = random.choice(tuples)
        if level >= 10:
            reward_time_base = REWARD_TIME_SEC * 2
        #Adjust the bonus reward timer based on the level
        reward_time_adjust = level * 2
        reward_time = reward_time_base - reward_time_adjust
        #Set start time
        prob_start = time.time()
        prob_prompt = "  Solve the problem:\n\n    {0} {2} {1} = ?\n\nEnter your answer".format(*work_on)
        if level >= 10:
            if work_on[0] >= work_on[1]:
                prob_prompt = "Solve the problem:\n\n{indent} {0:>4}\n{indent}{2}{1:>4}\n{indent}{flat:>4}\n\nEnter your answer".format(*work_on, indent='    ', flat='_____')
        ans_resp = get_valid_int(prompt=prob_prompt)
        prob_end = time.time()
        prob_dur = prob_end - prob_start
        correct_ans = get_ans(*work_on)
        if ans_resp == correct_ans[0]:
            ans_points = get_score_value(*correct_ans)
            score += ans_points
            reward_mins += ans_points * POINTS_TO_REWARD_VAL
            print(random.choice(CONGRATULATIONS).format(points=ans_points))
            if prob_dur <= reward_time:
                score += SCORING_MATRIX['bonus']
                reward_mins += POINTS_TO_REWARD_VAL * SCORING_MATRIX['bonus']
                print("You answered in {:.1f} seconds! Enjoy {} extra bonus points!".format(prob_dur, SCORING_MATRIX['bonus']))
                #This means you must master a problem twice before it is removed
                if work_on not in results['mastered']:
                    results['mastered'].append(work_on)
                else:
                    tuples.remove(work_on)
                if work_on in results['needs_work']:
                    print("CONGRATULATIONS!! You got one right that you got wrong before!")
                    results['needs_work'].remove(work_on)
                    tuples.append(work_on) # Add back to normal list of tuple problems so that mastery can be checked again
        elif ans_resp == None:
            print("Exiting")
            running = False
            continue
        else:
            print(random.choice(ENCOURAGEMENTS).format(answer=correct_ans[0]))
            if not work_on in results['needs_work']:
                results['needs_work'].append(work_on)
            if level < 10:
                while not get_valid_int(prompt="Show me you've see the answer. Enter it here") == correct_ans[0]:
                    print("The correct answer should be: {}".format(correct_ans[0]))
        if prob_end - START_TIME > MAX_MIN * 60:
            print("Time is UP!")
            running = False
        else:
            time.sleep(1.5)
            clear()
    print_results(results)
    print("\nFinal score: {}".format(score))
    try:
        text_input("Press 'Enter' to exit")
    except:
        sys.exit(1)
    print("Saving state file to: {}...".format(STATE_FILE))
    save_state({
        'results': results,
        'tuples': tuples,
        'score': score,
        'reward_mins': reward_mins,
        'rewards_enabled': rewards_enabled,
        'level': level,
        'operators': operators,
        'left_hand': left_hand,
        'right_hand': right_hand,
        'allow_sub_neg_ans': allow_sub_neg_ans,
        'allow_sub_mult_dbl_q': allow_sub_mult_dbl_q
    })

if __name__ == "__main__":
    PROFILE = None
    PROFILES = []
    LOAD_SAVE = False
    if not os.path.isdir(STATE_FILE_DIR):
        os.mkdir(STATE_FILE_DIR)
    if len(sys.argv) > 1:
        if sys.argv[1] == 'new':
            PROFILE = get_user_input(prompt='Enter the name of the new profile you want to create')
            STATE_FILE = '{}/{}-stats.json'.format(STATE_FILE_DIR, PROFILE)
            NEW_STATE = load_state(new=True)
            save_state(NEW_STATE)
            PROFILES = [ PROFILE ]
            LOAD_SAVE = True
        else:
            print("Unknown argument: {}".format(sys.argv[1]))
            sys.exit(1)
    START_TIME=time.time()
    if not PROFILE:
        # Load the profile selection
        PROFILES = [f[:-11] for f in os.listdir(STATE_FILE_DIR) if os.path.isfile('{}/{}'.format(STATE_FILE_DIR,f)) and f.endswith('-stats.json')]
        PROFILES.sort()
        if not PROFILES:
            PROFILE = get_user_input(prompt='No profile found, enter a name to create a new profile')
            STATE_FILE = '{}/{}-stats.json'.format(STATE_FILE_DIR, PROFILE)
            NEW_STATE = load_state(new=True)
            save_state(NEW_STATE)
        else:
            PROFILE = get_selection_menu(options=PROFILES, title="Select your profile to load")[0]
            STATE_FILE = '{}/{}-stats.json'.format(STATE_FILE_DIR, PROFILE)
            if os.path.isfile(STATE_FILE):
                if not get_user_input(prompt='Ready to load profile "{}". Would you like to load it to resume? (y/n)'.format(PROFILE), yesno=True):
                    if not get_user_input(prompt='Are you sure? All previous progress will be lost! (y/n)', yesno=True):
                        print("Ok, exiting!")
                        sys.exit(1)
                else:
                    LOAD_SAVE = True
    MAX_MIN = get_valid_int(minimum=1, maximum=90, default=MAX_MIN, prompt="How many minutes would you like to practice for? (default={default})")
    try:
        main(load_save=LOAD_SAVE)
    except KeyboardInterrupt:
        print("\nForced Exit!")
        sys.exit(1)
