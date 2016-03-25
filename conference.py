'''
Conference Track Management
- The conference has multiple tracks each of which has a morning and afternoon session.
- Each session contains multiple talks.
- Morning sessions begin at 9am and must finish by 12 noon, for lunch.
- Afternoon sessions begin at 1pm and must finish in time for the networking event.
- The networking event can start no earlier than 4:00 and no later than 5:00.
- All talk lengths are either in minutes (not hours) or lightning (5 minutes).
- Presenters will be very punctual; there needs to be no gap between sessions.
'''

import datetime
import re
import math
import sys
import logging
from random import shuffle

############################################################
#   Constants
############################################################

inputfile = sys.argv[1]
logging.basicConfig(stream=sys.stdout, level=logging.INFO) # set level to logging.DEBUG to display debug messages

# returns datetime object of hour o'clock on 1-1-2017 (arbitrary date)
def hour_oclock(hour):
    return datetime.datetime(2017, 1, 1, hour)

LUNCH_TIME = hour_oclock(12)
NETWORKING_TIME = hour_oclock(16)

MORNING_START_TIME = hour_oclock(9)
AFTERNOON_START_TIME = hour_oclock(13)

MORNING_TIME_MAX = 3 * 60
AFTERNOON_TIME_MAX = 4 * 60

############################################################
#   Talk and Session class definitions
############################################################

class Talk:
    def __init__(self, title):
        self.title = title.strip()
        self.duration = self.extract_duration(title) # int (minutes)

    def extract_duration(self, 
        title):
        dur_str = title.split()[-1]
        if dur_str == 'lightning':
            return 5
        return int(re.findall('\d+', dur_str)[0])

class Session:
    def __init__(self, track_id):
        self.track_num = track_id + 1
        self.talks = []
        self.filled_time = 0
        self.total_time = 0
        self.session_type = ''

    def is_not_possible(self):
        return (self.filled_time > self.total_time)

    def is_full(self):
        return (self.filled_time >= self.total_time)

    def add_talk(self, talk):
        self.filled_time += talk.duration
        if self.is_not_possible():
            self.filled_time -= talk.duration
            raise ValueError("Uh oh, can't fit <<{}>> into Track {}'s {} session".format(talk.title, self.track_num, self.session_type))
        else:
            self.talks.append(talk)
            logging.debug("Added <<{}>> to Track {}'s {} session.".format(talk.title, self.track_num, self.session_type))

class MorningSession(Session):
    def __init__(self, track_id):
        Session.__init__(self, track_id)
        self.total_time = MORNING_TIME_MAX
        self.session_type = "morning"

class AfternoonSession(Session):
    def __init__(self, track_id):
        Session.__init__(self, track_id)
        self.total_time = AFTERNOON_TIME_MAX
        self.session_type = "afternoon"

############################################################
#   Scheduling talks into conference's tracks and sessions
############################################################

#   Convert talks in input text to instances of Talk class
f = open(inputfile, 'r')
talks = []
for line in f:
    talks.append(Talk(line))

# Sort talks from longest to shortest
talks = sorted(talks, key=lambda talk: talk.duration, reverse=True)

# Calculate minimum number of tracks that all talks can be fitted into
total_duration = sum([talk.duration for talk in talks])
num_tracks = int(math.ceil(float(total_duration) / (MORNING_TIME_MAX + AFTERNOON_TIME_MAX)))

# Initialize lists of sessions for each track
morning_sessions = [MorningSession(i) for i in range(num_tracks)] # morning_sessions[0] accesses track 1's morning sessions
afternoon_sessions = [AfternoonSession(i) for i in range(num_tracks)]
sessions = morning_sessions + afternoon_sessions

'''
ALLOCATION ALGORITHM:
Iterate through all talks from longest to shortest, trying to place each talk in consecutive sessions 
(in the order of [track 1's morning session, track 2's morning session, ... , track 1's afternoon session, ...])
to fill up all sessions as evenly as possible with the longer talks first.
'''

current_session_index = 0
while(talks):
    talk = talks[0]
    while(True):
        session = sessions[current_session_index]
        if session.is_full():
            logging.debug("Track {}'s {} session is full; remove from tracks".format(session.track_num, session.session_type))
            sessions.remove(session)
            current_session_index = (current_session_index + 1) % (len(sessions)) # next session 
            continue
        current_session_index = (current_session_index + 1) % (len(sessions)) # next session 
        try:
            session.add_talk(talk) 
            talks.remove(talk) # talk added successfully; remove talk from talks
            break # move on to next talk in talks
        except ValueError, e:
            logging.debug(e) # couldn't add talk to this session, go through while() loop again for next session


############################################################
#   Randomize order of talks within sessions
############################################################
for session in sessions:
    shuffle(session.talks)

############################################################
#   Print final schedule
############################################################

def add_minutes(time, mins):
    return time + datetime.timedelta(minutes=mins)

def print_timing(time):
    return time.strftime('%I:%M%p')

def is_lunch_time(time):
    return time == LUNCH_TIME

def is_networking_time(time):
    return time >= NETWORKING_TIME

for track_id in range(num_tracks):
    print "Track {}:\n".format(track_id + 1)

    # Print this track's morning session talks.
    time = MORNING_START_TIME
    for talk in morning_sessions[track_id].talks:
        print "{} {}\n".format(print_timing(time), talk.title)
        time = add_minutes(time, talk.duration)
    
    if not is_lunch_time(time):
        print "{} Break\n".format(print_timing(time))
    print "12:00PM Lunch\n"

    # Print this track's afternoon session talks.
    time = AFTERNOON_START_TIME
    for talk in afternoon_sessions[track_id].talks:
        print "{} {}\n".format(print_timing(time), talk.title)
        time = add_minutes(time, talk.duration)
    
    if not is_networking_time(time):
        print "{} Break\n".format(print_timing(time))
        print "4:00PM Networking Event\n"
    else:
        print "{} Networking Event\n".format(print_timing(time))