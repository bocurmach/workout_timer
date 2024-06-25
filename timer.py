import msvcrt as mc
import sys
import time
from curses import wrapper
import curses

reps = 3


workouts = ('Planks (1 min)', 'Mountain climber 25x', 'Rows 10x', 'Push ups 10x', 'Horizontal pullaparts 25x')
#Ball links rechts | 10 full sets
#Row-Plank-Mountain climber mit beiden beinen)

def time_to_str(t_time: time, precision=1):
    hrs = int(t_time/3600)
    mns = int((t_time-hrs*3600)/60)
    secs = int(t_time-hrs*3600-mns*60)
    dots = int((t_time-hrs*3600-mns*60-secs)*10**precision)

    str_time = f"{hrs:02d}:{mns:02d}:{secs:02d}.{dots:01d}"
    return str_time


def write_sets(w_count):
    set_str = ''

    for i in range(w_count):
        set_str += 'I '

        if (i+1) % reps == 0:
            set_str += '  '

    return set_str


def write_breaks(b_count):
    set_str = ''

    for i in range(b_count):
        set_str += ' I'

        if (i+1) % reps == 0:
            set_str += '  '

    return set_str


def write_display(screen,
                  t_time_elapsed: time,
                  w_time_elapsed: time,
                  b_time_elapsed: time,
                  c_time_elapsed: time,
                  c_segment: str,
                  w_count: int,
                  b_count: int,
                  quit_next: bool):

    # display line count
    lines = list()

    lines.append(f"Total time elapsed:   {time_to_str(t_time_elapsed)}s\t\t\n")
    lines.append(f"Workout time elapsed: {time_to_str(w_time_elapsed)}s\t\t{write_sets(w_count)}\n")
    lines.append(f"Break time elapsed:   {time_to_str(b_time_elapsed)}s\t\t{write_breaks(b_count)}\n")
    lines.append(f"{(w_count-1)*100/(len(workouts)*reps):.0f}% done\n")

    last_line = f"Current {c_segment}: {time_to_str(c_time_elapsed)}s\t\t"

    if not quit_next:
        if c_segment == 'break':
            last_line += f"Get Ready for {workouts[int(w_count/reps)]}"
        else:
            last_line += f"Doing {workouts[int(b_count/reps)]}"

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
        screen.addstr(last_line, color_pair)

        screen.refresh()

        time.sleep(0.1)
    return lines


def workout(screen):

    workout_start = time.time()
    w_time_elapsed = 0.0
    b_time_elapsed = 0.0
    segment = 'workout'
    last_kh = time.time()

    w_count = 1
    b_count = 0

    can_go_back = False
    quit_next = False
    last_display = ""

    while True:
        c_time_elapsed = time.time() - last_kh

        if segment == 'workout':
            last_display = write_display(screen,
                                         time.time() - workout_start,
                                         w_time_elapsed + c_time_elapsed,
                                         b_time_elapsed,
                                         c_time_elapsed,
                                         segment,
                                         w_count,
                                         b_count,
                                         quit_next)
        elif segment == 'break':
            last_display = write_display(screen,
                                         time.time() - workout_start,
                                         w_time_elapsed,
                                         b_time_elapsed + c_time_elapsed,
                                         c_time_elapsed,
                                         segment,
                                         w_count,
                                         b_count,
                                         quit_next)

        if quit_next:
            break

        if mc.kbhit():
            ch = mc.getch()

            if ch == chr(27).encode(): # esc
                quit_next = True
                last_kh = time.time()
            elif ch == ' '.encode():
                can_go_back = True
                if segment == 'workout':
                    segment = 'break'
                    b_count += 1
                    w_time_elapsed += time.time() - last_kh
                elif segment == 'break':
                    segment = 'workout'
                    w_count += 1
                    b_time_elapsed += time.time() - last_kh
                last_kh = time.time()

                if b_count >= len(workouts)*reps:
                    quit_next = True
                    b_count -= 1
            elif ch == chr(8).encode() and can_go_back:
                can_go_back = False
                if segment == 'workout':
                    segment = 'break'
                    w_count -= 1
                    b_time_elapsed += time.time() - last_kh
                elif segment == 'break':
                    segment = 'workout'
                    b_count -= 1
                    w_time_elapsed += time.time() - last_kh

                last_kh = time.time()

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

    for workout in workouts:
        f.write(workout + ', ')
    f.write("times:\n")
    f.writelines(lines[:-1])
    f.write("------------------------------\n")
    f.write("\n")


def main():
    print('lets get cracking')
    screen = curses.initscr()
    print('lets get cracking')
    curses.start_color()
    print('lets get cracking')
    curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
    print('lets get cracking')
    last_lines = workout(screen)

    save_lines_to_file(last_lines)

    for line in last_lines[:-1]:
        print(line, end='')
    print('100% done')
    #print(f"total workout time: {time.time()-workout_start:.2f} s")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        reps = int(sys.argv[1])

    main()

