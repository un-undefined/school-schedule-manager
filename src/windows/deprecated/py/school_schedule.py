from datetime import datetime, date, timedelta

def _time(hour, minute):
    return datetime.combine(date.today(), datetime.min.time()).replace(hour=hour, minute=minute)

def strtime(string):
    if isinstance(string, datetime):
        return string
    h, m = string.split(":")
    return _time(int(h), int(m))

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def average_dt(dates):
    timestamps = [dt.timestamp() for dt in dates]

    avg_timestamp = sum(timestamps) / len(timestamps)
    avg_minutes = int(avg_timestamp // 60)

    floored_timestamp = avg_minutes * 60
    return datetime.fromtimestamp(floored_timestamp)

def print_block(block):
    print(str(block.start_time.time())[:-3], " ", str(block.end_time.time())[:-3], " ", block.course.cid.ljust(3), " ", block.block.block_type.ljust(20), block.course.name)

def print_schedule(schedule):
    for block in schedule:
        print_block(block)

# - courses -
class Course:
    def __init__(self, cid, nid, name, icon, color):
        self.cid = cid
        self.nid = nid
        self.name = name
        self.icon = icon
        self.accent_color = hex_to_rgb(color)
        self.icon_surf = None
        self.small_icon_surf = None
    
    def load_icon(self, surf, small_surf):
        self.icon_surf = surf
        self.small_icon_surf = small_surf

# - schedule block -
class Block:
    def __init__(self, start, end, block_type, block_name):
        self.start_time = strtime(start)
        self.end_time = strtime(end)
        self.block_type = block_type
        self.block_name = block_name
        self.total_time = self.end_time - self.start_time

    def copy_unmerged(self):
        block_type = self.block_type[:-2] if self.block_type[-2:] in ["_x", "_y"] else self.block_type
        return Block(self.start_time, self.end_time, block_type, self.block_name)

# - default fallback values 1 -
class BlockInfo:
    BLOCK_TIMES = {
        "normal": [
            Block("0:00", "8:20", "before_school", "Before School"),
            Block("8:20", "9:46", "class", "1st Block"),
            Block("9:46", "9:53", "transition", "Transition to 2nd Block"),
            Block("9:53", "11:19", "class", "2nd Block"),
            Block("11:19", "11:26", "transition", "Transition to 3rd Block"),
            Block("11:26", "13:22", "class_lunch", "3rd Block"),
            Block("13:22", "13:29", "transition", "Transition to 4th Block"),
            Block("13:29", "14:55", "class", "4th Block"),
            Block("14:55", "23:59", "end_of_school_day", "End of School Day"),
        ],
        "advisory": [
            Block("0:00", "8:20", "before_school", "Before School"),
            Block("8:20", "9:39", "class", "1st Block"),
            Block("9:39", "9:46", "transition", "Transition to 2nd Block"),
            Block("9:46", "11:05", "class", "2nd Block"),
            Block("11:05", "11:12", "transition", "Transition to Advisory"),
            Block("11:12", "11:37", "advisory", "Advisory"),
            Block("11:37", "11:44", "transition", "Transition to 3rd Block"),
            Block("11:44", "13:29", "class_lunch", "3rd Block"),
            Block("13:29", "13:36", "transition", "Transition to 4th Block"),
            Block("13:36", "14:55", "class", "4th Block"),
            Block("14:55", "23:59", "end_of_school_day", "End of School Day"),
        ],
        "short": [
            Block("0:00", "8:20", "before_school", "Before School"),
            Block("8:20", "9:19", "class", "1st Block"),
            Block("9:19", "9:26", "transition", "Transition to 2nd Block"),
            Block("9:26", "10:24", "class", "2nd Block"),
            Block("10:24", "10:31", "transition", "Transition to 3rd Block"),
            Block("10:31", "11:29", "class", "3rd Block"),
            Block("11:29", "11:36", "transition", "Transition to 4th Block"),
            Block("11:36", "12:35", "class", "4th Block"),
            Block("12:35", "23:59", "end_of_school_day", "End of School Day"),
        ],
        "break": [
            Block("0:00", "23:59", "no_school", "No School!")
        ]
    }

    LUNCH_TIMES = {
            "normal": [
                    Block("11:24", "11:54", "lunch", "1st Lunch"),
                    Block("11:54", "12:24", "lunch", "2nd Lunch"),
                    Block("12:09", "12:39", "lunch", "3rd Lunch"),
                    Block("12:24", "12:54", "lunch", "4th Lunch"),
                    Block("12:54", "13:24", "lunch", "5th Lunch")
                ],
            "advisory": [
                    Block("11:44", "12:14", "lunch", "1st Lunch"),
                    Block("12:09", "12:39", "lunch", "2nd Lunch"),
                    Block("12:26", "12:56", "lunch", "3rd Lunch"),
                    Block("12:34", "13:04", "lunch", "4th Lunch"),
                    Block("12:59", "13:29", "lunch", "5th Lunch")
                ]
        }

    CLASS_SCHEDULES = [
        ["1xA", "1yA", "3xA", "3yA", "5xA", "5yA", "7xA", "7yA"],
        ["2xB", "2yB", "4xB", "4yB", "6xB", "6yB", "8xB", "8yB"],
        ["3xC", "3yC", "1xC", "1yC", "7xC", "7yC", "5xC", "5yC"],
        ["4xD", "4yD", "2xD", "2yD", "8xD", "8yD", "6xD", "6yD"]
    ]

# - default fallback values 2 -
class ScheduleConfig:
    COURSES = [
        Course("1", "class", "Humanities", "book-open-text", "#D99B26"),
        Course("2", "class", "Humanities", "landmark", "#D99B26"),
        Course("3", "class", "Spanish III", "languages", "#8C46E6"),
        Course("4", "class", "Robotics", "bot", "#2CA5C4"),
        Course("5xA", "class", "Study Hall MINI", "notebook-pen", "#8C6A43"),
        Course("5yA", "class", "Biology III MINI", "germ", "#2EA84B"),
        Course("5xC", "class", "FLIGHT MINI", "plane-takeoff", "#5BB3DE"),
        Course("5yC", "class", "Study Hall MINI", "notebook-pen", "#8C6A43"),
        Course("6", "class", "Biology III", "microscope", "#2EA84B"),
        Course("7", "class", "Public Speaking", "speech", "#E64D80"),
        Course("8", "class", "Math (3-in-2)", "calculator", "#4C8BF5"),
        Course("A", "advisory", "Advisory", "users", "#D94E4E"),
        Course("L", "lunch", "Lunch", "hamburger", "#48B833"),
        Course("*", "transition", "Transition", "arrow-right-from-line", "#6B828A"),
        Course("/", "none", "None", "calendar-x", "#757B85"),
        Course("E", "end_of_school_day", "End of School Day", "log-out", "#C5C5C5"),
        Course("B", "before_school", "Before School", "alarm-clock", "#757B85"),
        Course("N", "no_school", "No School!", "party-popper", "#9A50E6")
    ]

    LUNCH_SCHEDULES = [3, 1, 1, 5]

# - class time -
class Class:
    def __init__(self, current_time, course, block, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.course = course
        self.block = block

        self.total_time = self.end_time - self.start_time
        
        if self.course.nid == "end_of_school_day":
            self.class_percent = 1
            self.time_remaining = ""
        elif self.end_time is not None and self.start_time is not None:
            total_duration = self.end_time - self.start_time
            elapsed_duration = current_time - self.start_time
            remaining_duration = total_duration - elapsed_duration
            remaining_seconds = max(0, int(remaining_duration.total_seconds()))

            if total_duration.total_seconds() == 0:
                self.class_percent = 1.0 if current_time >= self.end_time else 0.0
            else:
                self.class_percent = max(0.0, min(1.0, elapsed_duration.total_seconds() / total_duration.total_seconds()))

            hours, time_remainder = divmod(remaining_seconds, 3600)
            minutes, seconds = divmod(time_remainder, 60)

            if hours == 0:
                if minutes == 0:
                    self.time_remaining = f"{seconds}s"
                else:
                    self.time_remaining = f"{minutes}m {seconds:02d}s"
            else:
                self.time_remaining = f"{hours}h {minutes:02d}m {seconds:02d}s"
                
            if self.course.nid == "before_school":
                BEFORE_SCHOOL_DELAY = 15
                
                before_delay = (self.end_time - current_time).total_seconds() / 60
                self.class_percent = max(0, 1 - (before_delay / BEFORE_SCHOOL_DELAY))

    def copy_ctime(self, current_time, start, end):
        return Class(current_time, self.course, self.block, start, end)

# - single time -
class SchoolTime:
    def __init__(self, dt=None, special_days=None):
        self.dt = (datetime.now() - timedelta(seconds=1)) if dt is None else dt
        self.special_days = special_days or {}
        
        self.day_type = self.get_day_type(self.dt)
        self.school_day = self.get_school_day(self.dt)

    def _parse_date(self, d_str):
        if isinstance(d_str, date):
            return d_str
        
        current_year = datetime.now().year
        full_date_str = f"{current_year},{d_str}"
        
        return datetime.strptime(full_date_str, "%Y,%m,%d").date()

    get_day_type = def_get_day_type = lambda self, dt: self._resolve_day_type(dt)

    def _resolve_day_type(self, dt):
        current_date = dt.date()
        
        if current_date.weekday() >= 5:
            return "break"

        school_start = self.special_days.get("school_start")
        school_end = self.special_days.get("school_end")
        
        if school_start and school_end:
            current_year = current_date.year
            start_m, start_d = map(int, school_start.split(","))
            end_m, end_d = map(int, school_end.split(","))
            
            if current_date.month >= start_m:
                s_start = date(current_year, start_m, start_d)
                s_end = date(current_year + 1, end_m, end_d)
            else:
                s_start = date(current_year - 1, start_m, start_d)
                s_end = date(current_year, end_m, end_d)

            if not (s_start <= current_date <= s_end):
                return "break"

        no_school_list = self.special_days.get("no_school", [])
        for item in no_school_list:
            if isinstance(item, str):
                if self._parse_date(item) == current_date:
                    return "break"
            elif isinstance(item, dict):
                if self._parse_date(item["start"]) <= current_date <= self._parse_date(item["end"]):
                    return "break"

        short_days_list = self.special_days.get("short_days", [])
        for s_day in short_days_list:
            if self._parse_date(s_day) == current_date:
                return "short"
            
        if current_date.weekday() == self.special_days.get("advisory"):
            return "advisory"
            
        return "normal"

    def get_school_day(self, dt):
        current_date = dt.date()
        school_start = self.special_days.get("school_start")
        
        if not school_start:
            return 1

        start_date = self._parse_date(school_start)
        if current_date < start_date:
            return 1

        no_school_dates = set()
        for item in self.special_days.get("no_school", []):
            if isinstance(item, str):
                no_school_dates.add(self._parse_date(item))
            elif isinstance(item, dict):
                curr = self._parse_date(item["start"])
                end = self._parse_date(item["end"])
                while curr <= end:
                    no_school_dates.add(curr)
                    curr += timedelta(days=1)

        valid_days_count = 0
        iter_date = start_date
        while iter_date <= current_date:
            is_weekend = iter_date.weekday() >= 5
            is_holiday = iter_date in no_school_dates
            if not is_weekend and not is_holiday:
                valid_days_count += 1
            iter_date += timedelta(days=1)

        rotation_length = 4
        current_day_in_cycle = ((valid_days_count - 1) % rotation_length) + 1
        return max(1, current_day_in_cycle)

# - single schedule -
class Schedule:
    def __init__(self, schedule_config=None, block_info=None):
        self.courses = ScheduleConfig.COURSES if schedule_config is None else schedule_config.COURSES
        self.lunches = ScheduleConfig.LUNCH_SCHEDULES if schedule_config is None else schedule_config.LUNCH_SCHEDULES
        self.class_schedules = BlockInfo.CLASS_SCHEDULES if block_info is None else block_info.CLASS_SCHEDULES
        self.lunch_times = BlockInfo.LUNCH_TIMES if block_info is None else block_info.LUNCH_TIMES
        self.block_times = BlockInfo.BLOCK_TIMES if block_info is None else block_info.BLOCK_TIMES

    def get_course(self, name):
        for course in self.courses:
            if name in [course.nid, course.name]:
                return course
        return None

    def get_course_from_schedule(self, schedule):
        schedule = schedule.ljust(3, "-")
        for course in self.courses:
            cid = course.cid.ljust(3, "-")
            if cid[0] == schedule[0] and (cid[1] == schedule[1] or cid[1] == "-") and (cid[2] == schedule[2] or cid[2] == "-"):
                return course
        return None

    def get_none_class(self, dt):
        return Class(dt, self.get_course("none"), Block(_time(0, 0), _time(0, 0), "none", "None"), _time(0, 0), _time(0, 0))

    def get_no_school(self, dt):
        return Class(dt, self.get_course("no_school"), Block(_time(0, 0), _time(23, 59), "no_school", "No School!"), _time(0, 0), _time(23, 59))
    
    def current(self, schooltime=None, debug=False): # custom time
        if schooltime is None:
            schooltime = SchoolTime()
            
        school_day = schooltime.school_day
        day_type = schooltime.day_type
        dt = schooltime.dt

        if day_type == "no_school":
            return Current(self.get_no_school(dt), self.get_none_class(dt))

        current_schedule = self.block_times[day_type]

        # 1. split class blocks
        split_schedule = []
        for block in current_schedule:
            if "class" in block.block_type.split("_"):
                split_time = average_dt([block.start_time, block.end_time])
                split_schedule.append(Block(block.start_time, split_time, block.block_type + "_x", block.block_name + " (1st Half)"))
                split_schedule.append(Block(split_time, block.end_time, block.block_type + "_y", block.block_name + " (2nd Half)"))
            else:
                split_schedule.append(block)

        # 2. assign classes into blocks
        class_schedule = []
        class_block = 0
        for block in split_schedule:
            block_type = block.block_type
            if "class" in block_type.split("_"):
                course = self.get_course_from_schedule(self.class_schedules[school_day - 1][class_block])
                class_block += 1
            else:
                course = self.get_course(block_type)
            class_schedule.append(Class(dt, course, block, block.start_time, block.end_time))

        # 3. merge classes back together
        merged_schedule = []
        for class_ in class_schedule:
            if len(merged_schedule) > 0 and class_.course.cid == merged_schedule[-1].course.cid:
                merged_schedule.pop(-1)
                merged_schedule.append(Class(dt, class_.course, class_.block.copy_unmerged(), merged_schedule[-1].end_time, class_.end_time))
            else:
                merged_schedule.append(class_)

        # 4. find lunch and insert it
        if day_type not in ["short", "break"]:
            lunch_block = self.lunch_times[day_type][self.lunches[school_day - 1] - 1]
            lunch_wave = self.lunches[school_day - 1]
            lunch_course = self.get_course("lunch")

            final_schedule = []
            def insert_lunch():
                final_schedule.append(Class(dt, lunch_course, lunch_block, lunch_block.start_time, lunch_block.end_time))

            for i, class_ in enumerate(merged_schedule):
                block_type = class_.block.block_type.split("_")
                if "lunch" in block_type:
                    if "x" in block_type:
                        next_class = merged_schedule[i + 1]
                        half_time = ((next_class.end_time - class_.start_time) - (lunch_block.total_time)).total_seconds() // 120
                        remaining_time = (lunch_block.start_time - class_.start_time).total_seconds() / 60
                        if remaining_time <= 0:
                            insert_lunch()
                            final_schedule.append(class_.copy_ctime(dt, lunch_block.end_time, lunch_block.end_time + timedelta(minutes=half_time)))
                            final_schedule.append(next_class.copy_ctime(dt, lunch_block.end_time + timedelta(minutes=half_time), next_class.end_time))
                        elif remaining_time < half_time:
                            final_schedule.append(class_.copy_ctime(dt, class_.start_time, lunch_block.start_time))
                            insert_lunch()
                            final_schedule.append(class_.copy_ctime(dt, lunch_block.end_time, lunch_block.end_time + timedelta(minutes=half_time - remaining_time)))
                            final_schedule.append(next_class.copy_ctime(dt, next_class.end_time - timedelta(minutes=half_time), next_class.end_time))
                        elif remaining_time == half_time:
                            final_schedule.append(class_.copy_ctime(dt, class_.start_time, class_.start_time + timedelta(minutes=half_time)))
                            insert_lunch()
                            final_schedule.append(next_class.copy_ctime(dt, lunch_block.end_time, next_class.end_time))
                        elif remaining_time >= 2 * half_time:
                            final_schedule.append(class_.copy_ctime(dt, class_.start_time, class_.start_time + timedelta(minutes=half_time)))
                            final_schedule.append(next_class.copy_ctime(dt, class_.start_time + timedelta(minutes=half_time), next_class.end_time))
                            insert_lunch()
                        elif remaining_time > half_time:
                            final_schedule.append(class_.copy_ctime(dt, class_.start_time, class_.start_time + timedelta(minutes=half_time)))
                            final_schedule.append(next_class.copy_ctime(dt, class_.start_time + timedelta(minutes=half_time), lunch_block.start_time))
                            insert_lunch()
                            final_schedule.append(next_class.copy_ctime(dt, lunch_block.end_time, next_class.end_time))
                    elif "y" not in block_type:
                        if lunch_wave > 1:
                            final_schedule.append(class_.copy_ctime(dt, class_.start_time, lunch_block.start_time))
                        final_schedule.append(Class(dt, lunch_course, lunch_block, lunch_block.start_time, lunch_block.end_time))
                        if lunch_wave < 5:
                            final_schedule.append(class_.copy_ctime(dt, lunch_block.end_time, class_.end_time))
                else:
                    final_schedule.append(class_)
        else:
            final_schedule = merged_schedule

        # 5. assign current block and next block
        # NOTE: 1st/5th lunch overlaps with other classes; later one should override
        current_class = None
        next_class = None
        for block in final_schedule:
            if current_class is not None and next_class is None and block.course.nid != "transition":
                next_class = block
            if block.start_time <= dt <= block.end_time:
                current_class = block

        if next_class is None:
            next_class = self.get_none_class(dt)

        if debug:
            print_block(current_class)
            print_block(next_class)
    
            print("===", str(dt.time())[:-7], "===")
    
            for block in final_schedule:
                print_block(block)

        return Current(current_class, next_class, schooltime, final_schedule)

# - current point in time -
class Current:
    def __init__(self, current_class, next_class, schooltime, schedule):
        self.current_class = current_class
        self.next_class = next_class
        self.timeinfo = schooltime
        self.schedule = schedule
        
        pretty_date = {
                "break": "-",
                "advisory": ", Advisory",
                "normal": "",
                "short": ", Shortened"
            }
        day_type = self.timeinfo.day_type
        self.timeinfo_text = ("Day " + str(self.timeinfo.school_day) if day_type != "break" else "") + pretty_date[day_type]

# - schedule manager -
class ScheduleManager:
    def __init__(self):
        self.schedule = Schedule()
        self.reload("default")
        
    def reload(self, using, config=None):
        if using == "default":
            self.schedule.courses = ScheduleConfig.COURSES
            self.schedule.lunches = ScheduleConfig.LUNCH_SCHEDULES
            self.schedule.class_schedules = BlockInfo.CLASS_SCHEDULES
            self.schedule.lunch_times = BlockInfo.LUNCH_TIMES
            self.schedule.block_times = BlockInfo.BLOCK_TIMES
            
            self.special_days = {
                "school_start": "8,25",
                "school_end": "6,10",
                "advisory": 3,
                "no_school": ["9,7", "9,21", "10,12", "10,13", "10,21", "11,3", "11,25", "11,26", "11,27", "12,24", "12,25", "12,28", "12,29", "12,30", "12,31", "1,1", "1,18", "2,15", "2,16", "2,17", "2,18", "2,19", "3,26", "4,12", "4,13", "4,14", "4,15", "4,16", "5,31"],
                "short_days": ["9,9", "11,2", "11,19", "11,20", "11,23", "11,24", "12,9", "12,23", "1,13", "1,19", "1,20", "3,10", "4,7", "6,9", "6,10", "6,11" ]
            }
        elif using == "custom":
            # - courses -
            course_data = config["class_data"]["yearly_data"]["student_data"]["courses"]
            self.schedule.courses = [Course(c["period"], c["class_type"], c["class_name"], c["icon"], c["accent_color"]) for c in course_data]
            
            # - lunches -
            self.schedule.lunches = config["class_data"]["yearly_data"]["student_data"]["lunch_schedules"]
            
            # - day-to-day class schedules -
            self.schedule.class_schedules = config["class_data"]["constant_data"]["class_schedules"]
            
            # - lunch times / blocks -
            lunch_data = config["class_data"]["constant_data"]["lunch_times"]
            self.schedule.lunch_times = {schedule_type: [Block(l["block_start"], l["block_end"], "lunch", l["block_name"])for l in blocks] for schedule_type, blocks in lunch_data.items()}

            # - block times -
            block_data = config["class_data"]["constant_data"]["block_times"]
            self.schedule.block_times = {schedule_type: [Block(l["start_time"], l["end_time"], l["block_type"], l["block_name"])for l in blocks] for schedule_type, blocks in block_data.items()}
    
            self.special_days = {}
            special_dates = config["class_data"]["yearly_data"]["special_dates"]
            self.special_days["school_start"] = special_dates["school_bounds"][0]
            self.special_days["school_end"] = special_dates["school_bounds"][1]
            self.special_days["no_school"] = special_dates["no_school"]
            self.special_days["short_days"] = special_dates["short_days"]
            self.special_days["advisory"] = int(special_dates["advisory"])
    
    def current(self, dt=None):
        school_time = SchoolTime(dt=dt, special_days=self.special_days)
        return self.schedule.current(schooltime=school_time)