import pynput.keyboard as kb
import time
import curses
import threading
import json

CH = ''
lock = threading.Lock()


def load_workouts():
    f = open('workout_names.txt', 'r')

    f_workouts = list()
    f_workouts.append(list())
    cur_group = 0

    for line in f.readlines():
        line = line.removesuffix('\n')
        if line.strip(' ') == '':
            if len(f_workouts[cur_group]) > 0:
                cur_group += 1
                f_workouts.append(list())
        else:
            f_workouts[cur_group].append(line)

    if len(f_workouts[cur_group]) == 0:
        f_workouts.pop()

    return f_workouts


# workouts = [['Planks (1 min)', 'Horizontal pullaparts 25x'], ['Mountain climber 25x', 'Rows 10x', 'Push ups 10x']]
workouts = load_workouts()
# Ball links rechts | 10 full sets
# Row-Plank-Mountain climber mit beiden beinen)


def iterate_groups():
    for group_i in range(len(workouts)):
        for sub_i in range(len(workouts[group_i])*reps):
            yield group_i, sub_i % len(workouts[group_i])


def len_workouts():
    return len([x for x, y in iterate_groups()])


def get_cur_workout(workout_count):

    cur_workout = None
    cur_w_count = 0

    for group_i, sub_i in iterate_groups():
        if cur_w_count == workout_count:
            cur_workout = workouts[group_i][sub_i]
            break
        cur_w_count += 1

    return cur_workout


def time_to_str(t_time: float):
    hrs = int(t_time/3600)
    mns = int((t_time-hrs*3600)/60)
    secs = int(t_time-hrs*3600-mns*60)

    str_time = f"{hrs:02d}:{mns:02d}:{secs:02d}"
    return str_time


def write_is(i_count, segment, cur_segment):
    set_str = ''
    i_str = ''
    if segment == 'workout':
        i_str = 'I '
    elif segment == 'break':
        i_str = ' I'

    cur_i = 0
    cur_group = 0

    for group_i, sub_i in iterate_groups():
        if sub_i == 0 and len(set_str) > 0:
            set_str += ' '

            if group_i != cur_group:
                cur_group = group_i
                set_str += '| '

        cur_i += 1

        if cur_i > i_count:
            if cur_segment == segment:
                set_str += i_str
            break
        set_str += i_str
    return set_str


def write_display(screen,
                  t_time_elapsed: float,
                  w_time_elapsed: float,
                  b_time_elapsed: float,
                  c_time_elapsed: float,
                  c_segment: str,
                  w_count: int,
                  b_count: int,
                  quit_next: bool):

    # display line count
    lines = list()

    cur_workout = get_cur_workout(w_count)

    lines.append(f"Total time elapsed:   {
                 time_to_str(t_time_elapsed)}s        \n")
    lines.append(f"Workout time elapsed: {time_to_str(w_time_elapsed)}s        {
                 write_is(w_count, 'workout', c_segment)}\n")
    lines.append(f"Break time elapsed:   {time_to_str(b_time_elapsed)}s        {
                 write_is(b_count, 'break', c_segment)}\n")
    lines.append(f"{w_count*100/len_workouts():.0f}% done\n")
    cur_time_line = f"Current {c_segment}: {time_to_str(c_time_elapsed)}s\n"

    if not quit_next:
        if c_segment == 'break':
            cur_segment_line = f"Get Ready for {cur_workout}"
        else:
            cur_segment_line = f"Doing {cur_workout}"

        if c_segment == 'break':
            if c_time_elapsed >= 3*60:
                color_pair = curses.color_pair(curses.COLOR_GREEN)
            elif c_time_elapsed >= 1*60:
                color_pair = curses.color_pair(curses.COLOR_YELLOW)
            else:
                color_pair = curses.color_pair(curses.COLOR_RED)
        else:
            color_pair = curses.color_pair(curses.COLOR_WHITE)

        screen.clear()
        for line in lines:
            screen.addstr(line)
        screen.addstr(cur_time_line, color_pair)
        screen.addstr(cur_segment_line)

        screen.refresh()

        time.sleep(0.1)
    return lines


def CH_listener(key):
    global CH

    lock.acquire()
    CH = key
    lock.release()


def workout(screen):

    global CH

    workout_start = time.time()
    w_time_elapsed_list = list()
    b_time_elapsed_list = list()
    segment = 'workout'
    last_kh = time.time()

    quit_next = False
    last_display = ""

    listener = kb.Listener(on_press=CH_listener)
    listener.start()

    while True:
        c_time_elapsed = time.time() - last_kh

        if segment == 'workout':
            last_display = write_display(screen,
                                         time.time() - workout_start,
                                         sum(w_time_elapsed_list) +
                                         c_time_elapsed,
                                         sum(b_time_elapsed_list),
                                         c_time_elapsed,
                                         segment,
                                         len(w_time_elapsed_list),
                                         len(b_time_elapsed_list),
                                         quit_next)
        elif segment == 'break':
            last_display = write_display(screen,
                                         time.time() - workout_start,
                                         sum(w_time_elapsed_list),
                                         sum(b_time_elapsed_list) +
                                         c_time_elapsed,
                                         c_time_elapsed,
                                         segment,
                                         len(w_time_elapsed_list),
                                         len(b_time_elapsed_list),
                                         quit_next)

        time.sleep(0.1)
        print(CH)
        if quit_next:
            break

        if CH == kb.Key.esc:
            quit_next = True
            last_kh = time.time()
        elif CH == kb.Key.space:
            if segment == 'workout':
                segment = 'break'
                w_time_elapsed_list.append(time.time() - last_kh)
            elif segment == 'break':
                segment = 'workout'
                b_time_elapsed_list.append(time.time() - last_kh)
            last_kh = time.time()

            if len(w_time_elapsed_list) >= len_workouts():
                quit_next = True
        elif CH == kb.Key.backspace:
            if segment == 'workout':
                segment = 'break'
                last_kh -= b_time_elapsed_list.pop()
            elif segment == 'break':
                segment = 'workout'
                last_kh -= w_time_elapsed_list.pop()

        lock.acquire()
        CH = ''
        lock.release()

    return last_display


def save_lines_to_file(lines):
    import datetime
    import os

    dy = datetime.datetime.today().day
    mnth = datetime.datetime.today().month
    yr = datetime.datetime.today().year

    hr = datetime.datetime.today().hour
    mn = datetime.datetime.today().minute

    dir_name = f"workouts"

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    f = open(os.path.join(dir_name, f"{yr:02}_{mnth:02}.txt"), 'a')

    f.write("------------------------------\n")
    f.write(f"Workout on: {dy:02}.{mnth:02}.{yr}, {hr:02}:{mn:02} : \n")
    f.write(f"workouts: ({reps} reps each)\n")

    f.write(str(workouts).replace('[[', '').replace(']]', '').replace(
        '], [', ' | ').replace("'", '') + '\n')

    f.writelines(lines[:-1])
    f.write("------------------------------\n")
    f.write("\n")


def main():
    screen = curses.initscr()
    curses.start_color()

    curses.init_pair(curses.COLOR_GREEN,
                     curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_YELLOW,
                     curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_WHITE,
                     curses.COLOR_WHITE, curses.COLOR_BLACK)
    last_lines = workout(screen)

    save_lines_to_file(last_lines)

    for line in last_lines[:-1]:
        print(line, end='')
    print('100% done')
    # print(f"total workout time: {time.time()-workout_start:.2f} s")


if __name__ == "__main__":

    reps = -1

    while reps <= 0:
        reps = int(input('how many reps each?\n'))

    main()
